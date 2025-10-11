"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";

const consentOptions = [
  { id: "genomicData", label: "Genomic Data", description: "Share your full genomic sequence for research." },
  { id: "clinicalTrials", label: "Clinical Trials", description: "Be contacted for relevant clinical trials." },
  { id: "imagingData", label: "Medical Imaging", description: "Allow use of anonymized X-rays, MRIs, etc." },
  { id: "healthRecords", label: "Electronic Health Records", description: "Share anonymized EHR data for population studies." },
  { id: "wearableData", label: "Wearable Device Data", description: "Contribute data from fitness trackers and smartwatches." },
];

export default function DashboardPage() {
  const [consent, setConsent] = useState({
    genomicData: true,
    clinicalTrials: false,
    imagingData: true,
    healthRecords: true,
    wearableData: false,
  });

  const handleConsentChange = (id: keyof typeof consent) => {
    setConsent((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="container mx-auto">
      <Card>
        <CardHeader>
          <CardTitle className="font-headline text-2xl">Patient Consent Dashboard</CardTitle>
          <CardDescription>Manage your data sharing permissions with granular control.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {consentOptions.map((option) => (
            <div key={option.id} className="flex items-center justify-between p-4 border rounded-lg">
              <div className="space-y-0.5">
                <Label htmlFor={option.id} className="text-base font-medium">{option.label}</Label>
                <p className="text-sm text-muted-foreground">{option.description}</p>
              </div>
              <Switch
                id={option.id}
                checked={consent[option.id as keyof typeof consent]}
                onCheckedChange={() => handleConsentChange(option.id as keyof typeof consent)}
              />
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
