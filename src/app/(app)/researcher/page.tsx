"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Search, 
  Database, 
  FileText, 
  Activity, 
  User, 
  Mail, 
  Building, 
  GraduationCap,
  Plus,
  History,
  BarChart3
} from 'lucide-react';
import { QueryBuilder } from '@/components/researcher/query-builder';
import { QueryStatusTracker } from '@/components/researcher/query-status';
import { QueryHistory } from '@/components/researcher/query-history';
import { ResultsViewer } from '@/components/researcher/results-viewer';
import { ResearchQueryService, QueryTemplate } from '@/lib/research-query-api';

export default function ResearcherPortalPage() {
  const [activeTab, setActiveTab] = useState('submit');
  const [selectedQueryId, setSelectedQueryId] = useState<string | null>(null);
  const [templates, setTemplates] = useState<QueryTemplate[]>([]);
  const [historyRefreshTrigger, setHistoryRefreshTrigger] = useState(0);

  const researcher = ResearchQueryService.getCurrentResearcher();

  useEffect(() => {
    // Load query templates
    const loadedTemplates = ResearchQueryService.getQueryTemplates();
    setTemplates(loadedTemplates);
  }, []);

  const handleQuerySubmit = (queryId: string) => {
    setSelectedQueryId(queryId);
    setActiveTab('status');
    setHistoryRefreshTrigger(prev => prev + 1);
  };

  const handleViewQuery = (queryId: string) => {
    setSelectedQueryId(queryId);
    setActiveTab('status');
  };

  const handleViewResults = (queryId: string) => {
    setSelectedQueryId(queryId);
    setActiveTab('results');
  };

  return (
    <div className="container mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold font-headline">Researcher Portal</h1>
          <p className="text-muted-foreground">
            Submit research queries and access anonymized healthcare datasets
          </p>
        </div>
        <Badge variant="secondary" className="text-sm">
          <GraduationCap className="h-4 w-4 mr-1" />
          Researcher Access
        </Badge>
      </div>

      {/* Researcher Profile Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Researcher Profile
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">{researcher.name}</p>
                <p className="text-xs text-muted-foreground">Principal Investigator</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Building className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">{researcher.institution}</p>
                <p className="text-xs text-muted-foreground">{researcher.department}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Mail className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">{researcher.email}</p>
                <p className="text-xs text-muted-foreground">Contact Email</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">{researcher.researcherId}</p>
                <p className="text-xs text-muted-foreground">Researcher ID</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="submit" className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Submit Query
          </TabsTrigger>
          <TabsTrigger value="status" className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Query Status
          </TabsTrigger>
          <TabsTrigger value="history" className="flex items-center gap-2">
            <History className="h-4 w-4" />
            Query History
          </TabsTrigger>
          <TabsTrigger value="results" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Results
          </TabsTrigger>
        </TabsList>

        {/* Submit Query Tab */}
        <TabsContent value="submit" className="space-y-6">
          <Alert>
            <Search className="h-4 w-4" />
            <AlertDescription>
              Use the query builder below to create structured research queries. All data will be 
              anonymized according to privacy regulations and your specified requirements.
            </AlertDescription>
          </Alert>
          
          <QueryBuilder 
            onQuerySubmit={handleQuerySubmit}
            templates={templates}
          />
        </TabsContent>

        {/* Query Status Tab */}
        <TabsContent value="status" className="space-y-6">
          {selectedQueryId ? (
            <QueryStatusTracker 
              queryId={selectedQueryId}
              onViewResults={handleViewResults}
            />
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Activity className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium mb-2">No Query Selected</h3>
                <p className="text-muted-foreground text-center mb-4">
                  Submit a new query or select an existing query from your history to view its status.
                </p>
                <div className="flex gap-2">
                  <Button onClick={() => setActiveTab('submit')}>
                    <Plus className="h-4 w-4 mr-2" />
                    Submit New Query
                  </Button>
                  <Button variant="outline" onClick={() => setActiveTab('history')}>
                    <History className="h-4 w-4 mr-2" />
                    View History
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Query History Tab */}
        <TabsContent value="history" className="space-y-6">
          <QueryHistory 
            onViewQuery={handleViewQuery}
            onViewResults={handleViewResults}
            refreshTrigger={historyRefreshTrigger}
          />
        </TabsContent>

        {/* Results Tab */}
        <TabsContent value="results" className="space-y-6">
          {selectedQueryId ? (
            <ResultsViewer queryId={selectedQueryId} />
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <BarChart3 className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium mb-2">No Results Selected</h3>
                <p className="text-muted-foreground text-center mb-4">
                  Select a completed query from your history to view its results and download the dataset.
                </p>
                <Button variant="outline" onClick={() => setActiveTab('history')}>
                  <History className="h-4 w-4 mr-2" />
                  View Query History
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}