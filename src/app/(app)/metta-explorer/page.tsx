"use client";

import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { KnowledgeGraphBrowser } from "@/components/metta/knowledge-graph-browser";
import { QueryInterface } from "@/components/metta/query-interface";
import { ReasoningPathDisplay } from "@/components/metta/reasoning-path-display";
import { SchemaExplorer } from "@/components/metta/schema-explorer";
import { QueryResultsExport } from "@/components/metta/query-results-export";
import { MeTTaResponse } from "@/lib/metta-api";

export default function MeTTaExplorerPage() {
  const [currentQuery, setCurrentQuery] = useState<MeTTaResponse | null>(null);
  const [selectedEntity, setSelectedEntity] = useState<string | null>(null);

  const handleQueryExecuted = (response: MeTTaResponse) => {
    setCurrentQuery(response);
  };

  const handleEntitySelected = (entityType: string, entityId: string) => {
    setSelectedEntity(`${entityType}:${entityId}`);
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">MeTTa Explorer</h1>
          <p className="text-muted-foreground">
            Explore the knowledge graph, execute queries, and visualize reasoning paths
          </p>
        </div>
      </div>

      <Tabs defaultValue="browser" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="browser">Knowledge Graph</TabsTrigger>
          <TabsTrigger value="query">Query Interface</TabsTrigger>
          <TabsTrigger value="reasoning">Reasoning Paths</TabsTrigger>
          <TabsTrigger value="schema">Schema Explorer</TabsTrigger>
          <TabsTrigger value="export">Export Results</TabsTrigger>
        </TabsList>

        <TabsContent value="browser" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Knowledge Graph Browser</CardTitle>
              <CardDescription>
                Interactive visualization of entities and relationships in the MeTTa knowledge graph
              </CardDescription>
            </CardHeader>
            <CardContent>
              <KnowledgeGraphBrowser 
                onEntitySelected={handleEntitySelected}
                selectedEntity={selectedEntity}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="query" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>MeTTa Query Interface</CardTitle>
              <CardDescription>
                Execute MeTTa queries with syntax highlighting and real-time validation
              </CardDescription>
            </CardHeader>
            <CardContent>
              <QueryInterface onQueryExecuted={handleQueryExecuted} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="reasoning" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Reasoning Path Display</CardTitle>
              <CardDescription>
                Step-by-step visualization of MeTTa reasoning processes and decision paths
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ReasoningPathDisplay 
                queryResponse={currentQuery}
                onStepSelected={(step) => console.log('Selected step:', step)}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="schema" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Schema Explorer</CardTitle>
              <CardDescription>
                Browse entity types, relationships, and schema definitions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <SchemaExplorer 
                onEntityTypeSelected={(entityType) => setSelectedEntity(entityType)}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="export" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Query Results Export</CardTitle>
              <CardDescription>
                Export and share query results in various formats
              </CardDescription>
            </CardHeader>
            <CardContent>
              <QueryResultsExport 
                queryResponse={currentQuery}
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}