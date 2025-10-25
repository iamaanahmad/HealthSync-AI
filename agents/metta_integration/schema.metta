; HealthSync MeTTa Knowledge Graph Schema
; Healthcare domain entities, relationships, and rules

; ============================================================================
; ENTITY DEFINITIONS
; ============================================================================

; Patient Entity
(: Patient Type)
(: patient-id (-> Patient String))
(: demographic-hash (-> Patient String))
(: created-at (-> Patient DateTime))
(: active-status (-> Patient Bool))

; Consent Record Entity
(: ConsentRecord Type)
(: consent-id (-> ConsentRecord String))
(: patient-ref (-> ConsentRecord Patient))
(: data-type-ref (-> ConsentRecord DataType))
(: research-category-ref (-> ConsentRecord ResearchCategory))
(: consent-granted (-> ConsentRecord Bool))
(: expiry-date (-> ConsentRecord DateTime))
(: last-updated (-> ConsentRecord DateTime))

; Data Type Entity
(: DataType Type)
(: type-id (-> DataType String))
(: type-name (-> DataType String))
(: sensitivity-level (-> DataType String))
(: required-permissions (-> DataType (List String)))

; Research Category Entity
(: ResearchCategory Type)
(: category-id (-> ResearchCategory String))
(: category-name (-> ResearchCategory String))
(: ethics-requirements (-> ResearchCategory String))
(: allowed-data-types (-> ResearchCategory (List String)))

; Privacy Rule Entity
(: PrivacyRule Type)
(: rule-id (-> PrivacyRule String))
(: rule-name (-> PrivacyRule String))
(: applies-to-data-type (-> PrivacyRule DataType))
(: anonymization-method (-> PrivacyRule AnonymizationMethod))
(: k-anonymity-threshold (-> PrivacyRule Int))

; Anonymization Method Entity
(: AnonymizationMethod Type)
(: method-id (-> AnonymizationMethod String))
(: method-name (-> AnonymizationMethod String))
(: technique (-> AnonymizationMethod String))
(: privacy-level (-> AnonymizationMethod String))

; ============================================================================
; RELATIONSHIP DEFINITIONS
; ============================================================================

; Patient has consent records
(: has-consent (-> Patient ConsentRecord Bool))

; Consent covers data types
(: covers-data-type (-> ConsentRecord DataType Bool))

; Consent allows research categories
(: allows-research-category (-> ConsentRecord ResearchCategory Bool))

; Privacy rules apply to data types
(: privacy-rule-applies (-> PrivacyRule DataType Bool))

; Research category requires data types
(: requires-data-type (-> ResearchCategory DataType Bool))

; ============================================================================
; CONSENT VALIDATION RULES
; ============================================================================

; Rule: Check if patient has valid consent for data type and research category
(= (has-valid-consent $patient $data-type $research-category)
   (and
      (has-consent $patient $consent)
      (consent-granted $consent True)
      (covers-data-type $consent $data-type)
      (allows-research-category $consent $research-category)
      (not (is-expired $consent))))

; Rule: Check if consent is expired
(= (is-expired $consent)
   (let $expiry (expiry-date $consent)
      (< $expiry (current-time))))

; Rule: Check if consent is active
(= (is-active-consent $consent)
   (and
      (consent-granted $consent True)
      (not (is-expired $consent))))

; ============================================================================
; ETHICS COMPLIANCE RULES
; ============================================================================

; Rule: Validate research query meets ethical requirements
(= (meets-ethical-requirements $research-category $data-types)
   (and
      (all-data-types-allowed $research-category $data-types)
      (has-ethics-approval $research-category)))

; Rule: Check if all requested data types are allowed for research category
(= (all-data-types-allowed $research-category $data-types)
   (forall $dt $data-types
      (member $dt (allowed-data-types $research-category))))

; Rule: Verify ethics approval exists
(= (has-ethics-approval $research-category)
   (not (= (ethics-requirements $research-category) "")))

; ============================================================================
; PRIVACY RULES
; ============================================================================

; Rule: Get applicable privacy rule for data type
(= (get-privacy-rule $data-type)
   (let $rule (find-rule $data-type)
      (if (privacy-rule-applies $rule $data-type)
          $rule
          (default-privacy-rule))))

; Rule: Check if data requires high-level anonymization
(= (requires-high-anonymization $data-type)
   (= (sensitivity-level $data-type) "high"))

; Rule: Validate k-anonymity threshold
(= (meets-k-anonymity $data-type $k-value)
   (let $rule (get-privacy-rule $data-type)
      (>= $k-value (k-anonymity-threshold $rule))))

; Rule: Select anonymization method based on sensitivity
(= (select-anonymization-method $data-type)
   (if (requires-high-anonymization $data-type)
       (high-security-method)
       (standard-method)))

; ============================================================================
; RECURSIVE GRAPH TRAVERSAL RULES
; ============================================================================

; Rule: Find all consents for a patient (recursive)
(= (find-all-consents $patient)
   (match &self (has-consent $patient $consent)
      $consent))

; Rule: Find all patients with consent for specific research (recursive)
(= (find-consenting-patients $data-type $research-category)
   (match &self (has-valid-consent $patient $data-type $research-category)
      $patient))

; Rule: Traverse consent relationships to find applicable data
(= (traverse-consent-chain $patient $research-category)
   (let $consents (find-all-consents $patient)
      (filter (lambda $c (and
         (is-active-consent $c)
         (allows-research-category $c $research-category)))
         $consents)))

; ============================================================================
; NESTED QUERY SUPPORT
; ============================================================================

; Complex query: Find all valid data access permissions
(= (query-data-access-permissions $patient $research-category)
   (let $consents (traverse-consent-chain $patient $research-category)
      (map (lambda $c
         (tuple
            (data-type-ref $c)
            (get-privacy-rule (data-type-ref $c))))
         $consents)))

; Complex query: Validate complete research request
(= (validate-research-request $patient $data-types $research-category)
   (and
      (meets-ethical-requirements $research-category $data-types)
      (forall $dt $data-types
         (has-valid-consent $patient $dt $research-category))
      (forall $dt $data-types
         (meets-k-anonymity $dt 5))))

; ============================================================================
; HELPER FUNCTIONS
; ============================================================================

; Get current timestamp
(= (current-time) (get-timestamp))

; Default privacy rule for unspecified data types
(= (default-privacy-rule)
   (new-privacy-rule "default" "Standard Privacy" 5 "hash"))

; Create tuple for structured results
(= (tuple $a $b) (cons $a (cons $b ())))

; Filter list based on predicate
(= (filter $pred ()) ())
(= (filter $pred (cons $head $tail))
   (if ($pred $head)
       (cons $head (filter $pred $tail))
       (filter $pred $tail)))

; Map function over list
(= (map $fn ()) ())
(= (map $fn (cons $head $tail))
   (cons ($fn $head) (map $fn $tail)))

; Check if element is member of list
(= (member $x ()) False)
(= (member $x (cons $head $tail))
   (if (= $x $head)
       True
       (member $x $tail)))

; Forall quantifier
(= (forall $x () $pred) True)
(= (forall $x (cons $head $tail) $pred)
   (and ($pred $head) (forall $x $tail $pred)))
