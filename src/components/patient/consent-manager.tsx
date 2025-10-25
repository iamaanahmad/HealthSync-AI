"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { 
  Shield, 
  Clock, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  RefreshCw,
  History
} from 'lucide-react';
import { 
  PatientConsentApi, 
  DataTypes, 
  ResearchCategories,
  type ConsentRecord,
  type ConsentUpdate 
} from '@/lib/patient-consent-api';
import { AuthService } from '@/lib/auth';
import { useToast } from '@/hooks/use-toast';
import { format } from 'date-fns';

interface ConsentManagerProps {
  onConsentChange?: (consents: ConsentRecord[]) => void;
}

export function ConsentManager({ onConsentChange }: ConsentManagerProps) {
  const [consents, setConsents] = useState<ConsentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const loadConsents = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const session = AuthService.getCurrentSession();
      if (!session?.patientId) {
        throw new Error('No patient session found');
      }

      const result = await PatientConsentApi.getPatientConsents(session.patientId);
      
      if (result.success && result.data) {
        setConsents(result.data);
        onConsentChange?.(result.data);
      } else {
        throw new Error(result.error || 'Failed to load consents');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load consents';
      setError(errorMessage);
      toast({
        title: 'Error Loading Consents',
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConsents();
  }, []);

  const handleConsentToggle = async (dataType: string, researchCategory: string, currentValue: boolean) => {
    const updateKey = `${dataType}-${researchCategory}`;
    
    try {
      setUpdating(updateKey);
      
      const session = AuthService.getCurrentSession();
      if (!session?.patientId) {
        throw new Error('No patient session found');
      }

      const update: ConsentUpdate = {
        patientId: session.patientId,
        dataType,
        researchCategory,
        consentGranted: !currentValue,
      };

      const result = await PatientConsentApi.updateConsent(update);
      
      if (result.success && result.data) {
        // Update the local state
        setConsents(prev => {
          const updated = prev.map(consent => 
            consent.dataType === dataType && consent.researchCategory === researchCategory
              ? result.data!
              : consent
          );
          
          // If it's a new consent record, add it
          if (!prev.some(c => c.dataType === dataType && c.researchCategory === researchCategory)) {
            updated.push(result.data!);
          }
          
          onConsentChange?.(updated);
          return updated;
        });

        toast({
          title: 'Consent Updated',
          description: `${PatientConsentApi.getDataTypeLabel(dataType)} consent for ${PatientConsentApi.getResearchCategoryLabel(researchCategory)} has been ${!currentValue ? 'granted' : 'revoked'}.`,
        });
      } else {
        throw new Error(result.error || 'Failed to update consent');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update consent';
      toast({
        title: 'Error Updating Consent',
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setUpdating(null);
    }
  };

  const getConsentValue = (dataType: string, researchCategory: string): boolean => {
    const consent = consents.find(c => c.dataType === dataType && c.researchCategory === researchCategory);
    return consent?.consentGranted ?? false;
  };

  const getExpiringConsents = () => {
    return consents.filter(consent => 
      consent.consentGranted && PatientConsentApi.isConsentExpiringSoon(consent)
    );
  };

  const formatLastUpdated = (dateString: string) => {
    try {
      return format(new Date(dateString), 'MMM d, yyyy \'at\' h:mm a');
    } catch {
      return dateString;
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center space-x-2">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span>Loading consent preferences...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              {error}
              <Button 
                variant="outline" 
                size="sm" 
                className="ml-4" 
                onClick={loadConsents}
              >
                Retry
              </Button>
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  const expiringConsents = getExpiringConsents();

  return (
    <div className="space-y-6">
      {/* Expiration Warnings */}
      {expiringConsents.length > 0 && (
        <Alert>
          <Clock className="h-4 w-4" />
          <AlertDescription>
            <div className="space-y-2">
              <p className="font-medium">Consent Expiration Notice</p>
              <p>The following consents will expire soon:</p>
              <ul className="list-disc list-inside space-y-1">
                {expiringConsents.map(consent => (
                  <li key={consent.consentId} className="text-sm">
                    {PatientConsentApi.getDataTypeLabel(consent.dataType)} for {PatientConsentApi.getResearchCategoryLabel(consent.researchCategory)} 
                    <span className="text-muted-foreground ml-1">
                      (expires {format(new Date(consent.expiryDate), 'MMM d, yyyy')})
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Consent Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Data Sharing Consent
          </CardTitle>
          <CardDescription>
            Control which types of data can be shared for different research categories. 
            Changes take effect immediately and are logged for your records.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {Object.entries(DataTypes).map(([key, dataType]) => (
            <div key={dataType}>
              <h3 className="text-lg font-semibold mb-3">
                {PatientConsentApi.getDataTypeLabel(dataType)}
              </h3>
              <div className="grid gap-4">
                {Object.entries(ResearchCategories).map(([categoryKey, researchCategory]) => {
                  const consentValue = getConsentValue(dataType, researchCategory);
                  const updateKey = `${dataType}-${researchCategory}`;
                  const isUpdating = updating === updateKey;
                  const consent = consents.find(c => c.dataType === dataType && c.researchCategory === researchCategory);
                  
                  return (
                    <div key={researchCategory} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="space-y-1 flex-1">
                        <div className="flex items-center gap-2">
                          <Label htmlFor={updateKey} className="text-base font-medium">
                            {PatientConsentApi.getResearchCategoryLabel(researchCategory)}
                          </Label>
                          {consentValue ? (
                            <Badge variant="default" className="text-xs">
                              <CheckCircle className="w-3 h-3 mr-1" />
                              Granted
                            </Badge>
                          ) : (
                            <Badge variant="secondary" className="text-xs">
                              <XCircle className="w-3 h-3 mr-1" />
                              Not Granted
                            </Badge>
                          )}
                        </div>
                        {consent && (
                          <p className="text-sm text-muted-foreground">
                            Last updated: {formatLastUpdated(consent.lastUpdated)}
                            {consent.expiryDate && (
                              <span className="ml-2">
                                • Expires: {format(new Date(consent.expiryDate), 'MMM d, yyyy')}
                              </span>
                            )}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center space-x-2">
                        {isUpdating && <RefreshCw className="h-4 w-4 animate-spin" />}
                        <Switch
                          id={updateKey}
                          checked={consentValue}
                          onCheckedChange={() => handleConsentToggle(dataType, researchCategory, consentValue)}
                          disabled={isUpdating}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
              {Object.keys(DataTypes).indexOf(key) < Object.keys(DataTypes).length - 1 && (
                <Separator className="mt-6" />
              )}
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Consent Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="h-5 w-5" />
            Consent Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {consents.filter(c => c.consentGranted).length}
              </div>
              <div className="text-sm text-muted-foreground">Active Consents</div>
            </div>
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-orange-600">
                {expiringConsents.length}
              </div>
              <div className="text-sm text-muted-foreground">Expiring Soon</div>
            </div>
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {consents.length}
              </div>
              <div className="text-sm text-muted-foreground">Total Records</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}