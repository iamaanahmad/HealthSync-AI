"use client";

import { useState } from 'react';
import { AuthGuard } from '@/components/auth/auth-guard';
import { ProfileCard } from '@/components/patient/profile-card';
import { ConsentManager } from '@/components/patient/consent-manager';
import { ConsentHistory } from '@/components/patient/consent-history';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import type { ConsentRecord } from '@/lib/patient-consent-api';

export default function DashboardPage() {
  const [consentRefreshTrigger, setConsentRefreshTrigger] = useState(0);

  const handleConsentChange = (consents: ConsentRecord[]) => {
    // Trigger refresh of consent history when consents change
    setConsentRefreshTrigger(prev => prev + 1);
  };

  return (
    <AuthGuard>
      <div className="container mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold font-headline">Patient Dashboard</h1>
            <p className="text-muted-foreground">
              Manage your profile and data sharing preferences with full control
            </p>
          </div>
        </div>

        <Tabs defaultValue="consent" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="consent">Consent Management</TabsTrigger>
            <TabsTrigger value="history">Consent History</TabsTrigger>
            <TabsTrigger value="profile">Profile & Authentication</TabsTrigger>
          </TabsList>

          <TabsContent value="consent" className="space-y-6">
            <ConsentManager onConsentChange={handleConsentChange} />
          </TabsContent>

          <TabsContent value="history" className="space-y-6">
            <ConsentHistory refreshTrigger={consentRefreshTrigger} />
          </TabsContent>

          <TabsContent value="profile" className="space-y-6">
            <ProfileCard />
          </TabsContent>
        </Tabs>
      </div>
    </AuthGuard>
  );
}
