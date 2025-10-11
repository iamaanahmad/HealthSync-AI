"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Search, Share2 } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

const schemas = [
  {
    id: "patientSchema",
    name: "Patient Schema",
    content: `{
  "@context": "http://schema.org/",
  "@type": "Patient",
  "name": "string",
  "birthDate": "date",
  "gender": "string"
}`,
  },
  {
    id: "consentSchema",
    name: "Consent Schema",
    content: `{
  "@context": "http://schema.org/",
  "@type": "Consent",
  "patientId": "string",
  "dataTypes": ["string"],
  "purpose": "string",
  "isGranted": "boolean"
}`,
  },
];

const rules = [
  {
    id: "ethicsRule1",
    name: "Ethics Rule: Data Minimization",
    content: `(= (can_access researcher data)
   (and (has_consent patient data)
        (is_minimal data research_purpose)))`,
  },
];

export default function MettaExplorerPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [query, setQuery] = useState(
    "(match (consent patient_123) $c)"
  );
  const [results, setResults] = useState<string | null>(null);

  const handleQuery = () => {
    setIsLoading(true);
    setResults(null);
    setTimeout(() => {
      setResults(`Path Found:
1. (match (consent patient_123) $c)
2. --> Loading patient_123 consent from MeTTa store.
3. --> Found consent: { dataTypes: ['genomic', 'imaging'], purpose: 'cancer_research' }
4. --> Result: $c = { dataTypes: ['genomic', 'imaging'], purpose: 'cancer_research' }`);
      setIsLoading(false);
    }, 1500);
  };

  return (
    <div className="container mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
      <div className="space-y-8">
        <Card>
          <CardHeader>
            <CardTitle className="font-headline text-2xl">
              MeTTa Explorer
            </CardTitle>
            <CardDescription>
              Browse medical schemas, ethical rules, and test queries against
              the knowledge graph.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value="schemas">
                <AccordionTrigger>Medical Schemas</AccordionTrigger>
                <AccordionContent className="space-y-4">
                  {schemas.map((schema) => (
                    <div key={schema.id}>
                      <h4 className="font-medium mb-2">{schema.name}</h4>
                      <pre className="p-4 rounded-md bg-muted text-xs whitespace-pre-wrap">
                        <code>{schema.content}</code>
                      </pre>
                    </div>
                  ))}
                </AccordionContent>
              </AccordionItem>
              <AccordionItem value="rules">
                <AccordionTrigger>Ethical & Governance Rules</AccordionTrigger>
                <AccordionContent className="space-y-4">
                  {rules.map((rule) => (
                    <div key={rule.id}>
                      <h4 className="font-medium mb-2">{rule.name}</h4>
                       <pre className="p-4 rounded-md bg-muted text-xs whitespace-pre-wrap">
                        <code>{rule.content}</code>
                      </pre>
                    </div>
                  ))}
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-8">
        <Card>
          <CardHeader>
            <CardTitle className="font-headline text-2xl">
              Test Query
            </CardTitle>
            <CardDescription>
              Submit a MeTTa query to see the reasoning path.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter MeTTa query..."
              className="min-h-[100px] font-mono text-sm"
            />
          </CardContent>
          <CardFooter>
            <Button onClick={handleQuery} disabled={isLoading}>
              {isLoading ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Search className="mr-2 h-4 w-4" />
              )}
              Run Query
            </Button>
          </CardFooter>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="font-headline flex items-center gap-2">
              <Share2 /> Reasoning Path
            </CardTitle>
            <CardDescription>
              The result of your query and the steps taken will appear here.
            </CardDescription>
          </CardHeader>
          <CardContent className="min-h-[200px] font-mono text-xs">
            {isLoading && (
              <div className="space-y-3">
                <Skeleton className="h-4 w-4/5" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            )}
            {results && !isLoading && (
              <pre className="whitespace-pre-wrap leading-relaxed">
                {results}
              </pre>
            )}
            {!results && !isLoading && (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                <p>Results will be displayed here.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
