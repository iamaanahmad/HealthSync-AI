"use client";

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Database, 
  Search, 
  GitBranch, 
  FileText, 
  Link, 
  Hash,
  Type,
  Key,
  RefreshCw,
  Eye,
  Code
} from "lucide-react";
import { mettaAPI, EntitySchema } from "@/lib/metta-api";
import { useToast } from "@/hooks/use-toast";

interface SchemaExplorerProps {
  onEntityTypeSelected: (entityType: string) => void;
}

interface RelationshipGraph {
  nodes: Array<{
    id: string;
    label: string;
    type: 'entity' | 'relationship';
    entityType?: string;
  }>;
  edges: Array<{
    source: string;
    target: string;
    label: string;
    cardinality: string;
  }>;
}

export function SchemaExplorer({ onEntityTypeSelected }: SchemaExplorerProps) {
  const [schemas, setSchemas] = useState<EntitySchema[]>([]);
  const [selectedSchema, setSelectedSchema] = useState<EntitySchema | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [relationshipGraph, setRelationshipGraph] = useState<RelationshipGraph | null>(null);
  const { toast } = useToast();

  const loadSchemas = useCallback(async () => {
    try {
      setLoading(true);
      const schemasData = await mettaAPI.getEntitySchemas();
      setSchemas(schemasData);
      
      if (schemasData.length > 0 && !selectedSchema) {
        setSelectedSchema(schemasData[0]);
      }
      
      // Generate relationship graph
      generateRelationshipGraph(schemasData);
    } catch (error) {
      console.error('Failed to load entity schemas:', error);
      toast({
        title: "Error",
        description: "Failed to load entity schemas",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [selectedSchema, toast]);

  const generateRelationshipGraph = (schemas: EntitySchema[]) => {
    const nodes: RelationshipGraph['nodes'] = [];
    const edges: RelationshipGraph['edges'] = [];

    // Add entity nodes
    schemas.forEach(schema => {
      nodes.push({
        id: schema.entity_type,
        label: schema.entity_type,
        type: 'entity',
        entityType: schema.entity_type
      });
    });

    // Add relationship edges
    schemas.forEach(schema => {
      schema.relationships.forEach(rel => {
        edges.push({
          source: schema.entity_type,
          target: rel.target_type,
          label: rel.name,
          cardinality: rel.cardinality
        });
      });
    });

    setRelationshipGraph({ nodes, edges });
  };

  const getFieldTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'string':
        return <Type className="h-4 w-4 text-blue-500" />;
      case 'number':
      case 'int':
      case 'integer':
        return <Hash className="h-4 w-4 text-green-500" />;
      case 'boolean':
      case 'bool':
        return <Database className="h-4 w-4 text-purple-500" />;
      case 'datetime':
      case 'date':
        return <FileText className="h-4 w-4 text-orange-500" />;
      case 'array':
      case 'list':
        return <GitBranch className="h-4 w-4 text-red-500" />;
      default:
        return <Type className="h-4 w-4 text-gray-500" />;
    }
  };

  const getFieldTypeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'string':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'number':
      case 'int':
      case 'integer':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'boolean':
      case 'bool':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'datetime':
      case 'date':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'array':
      case 'list':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getCardinalityColor = (cardinality: string) => {
    switch (cardinality) {
      case 'one-to-one':
        return 'bg-blue-100 text-blue-800';
      case 'one-to-many':
        return 'bg-green-100 text-green-800';
      case 'many-to-one':
        return 'bg-orange-100 text-orange-800';
      case 'many-to-many':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const filteredSchemas = schemas.filter(schema =>
    schema.entity_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
    schema.fields.some(field => 
      field.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      field.type.toLowerCase().includes(searchTerm.toLowerCase())
    )
  );

  const handleSchemaSelect = (schema: EntitySchema) => {
    setSelectedSchema(schema);
    onEntityTypeSelected(schema.entity_type);
  };

  useEffect(() => {
    loadSchemas();
  }, [loadSchemas]);

  return (
    <div className="space-y-6">
      {/* Schema Overview */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Schema Overview
          </CardTitle>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={loadSchemas}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">{schemas.length}</div>
              <div className="text-sm text-muted-foreground">Entity Types</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {schemas.reduce((sum, schema) => sum + schema.fields.length, 0)}
              </div>
              <div className="text-sm text-muted-foreground">Total Fields</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {schemas.reduce((sum, schema) => sum + schema.relationships.length, 0)}
              </div>
              <div className="text-sm text-muted-foreground">Relationships</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {schemas.reduce((sum, schema) => sum + schema.fields.filter(f => f.required).length, 0)}
              </div>
              <div className="text-sm text-muted-foreground">Required Fields</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Entity Types List */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Entity Types</CardTitle>
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search schemas..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8"
                />
              </div>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-96">
                <div className="space-y-2">
                  {filteredSchemas.map((schema) => (
                    <div
                      key={schema.entity_type}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedSchema?.entity_type === schema.entity_type
                          ? 'border-primary bg-primary/5'
                          : 'border-border hover:border-primary/50 hover:bg-muted/50'
                      }`}
                      onClick={() => handleSchemaSelect(schema)}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <Database className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">{schema.entity_type}</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <span>{schema.fields.length} fields</span>
                        <span>•</span>
                        <span>{schema.relationships.length} relations</span>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* Schema Details */}
        <div className="lg:col-span-2">
          {selectedSchema ? (
            <Tabs defaultValue="fields" className="space-y-4">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="fields">Fields</TabsTrigger>
                <TabsTrigger value="relationships">Relationships</TabsTrigger>
                <TabsTrigger value="graph">Schema Graph</TabsTrigger>
              </TabsList>

              <TabsContent value="fields">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <FileText className="h-5 w-5" />
                      {selectedSchema.entity_type} Fields
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ScrollArea className="h-96">
                      <div className="space-y-3">
                        {selectedSchema.fields.map((field) => (
                          <div
                            key={field.name}
                            className="p-4 rounded-lg border bg-card"
                          >
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                {getFieldTypeIcon(field.type)}
                                <span className="font-medium">{field.name}</span>
                                {field.required && (
                                  <Key className="h-3 w-3 text-red-500" />
                                )}
                              </div>
                              <Badge 
                                variant="outline" 
                                className={getFieldTypeColor(field.type)}
                              >
                                {field.type}
                              </Badge>
                            </div>
                            
                            {field.description && (
                              <p className="text-sm text-muted-foreground mb-2">
                                {field.description}
                              </p>
                            )}
                            
                            <div className="flex items-center gap-2">
                              {field.required && (
                                <Badge variant="destructive" className="text-xs">
                                  Required
                                </Badge>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="relationships">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Link className="h-5 w-5" />
                      {selectedSchema.entity_type} Relationships
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ScrollArea className="h-96">
                      {selectedSchema.relationships.length > 0 ? (
                        <div className="space-y-3">
                          {selectedSchema.relationships.map((rel, index) => (
                            <div
                              key={index}
                              className="p-4 rounded-lg border bg-card"
                            >
                              <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-2">
                                  <GitBranch className="h-4 w-4 text-muted-foreground" />
                                  <span className="font-medium">{rel.name}</span>
                                </div>
                                <Badge 
                                  variant="outline"
                                  className={getCardinalityColor(rel.cardinality)}
                                >
                                  {rel.cardinality}
                                </Badge>
                              </div>
                              
                              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                <span>{selectedSchema.entity_type}</span>
                                <span>→</span>
                                <span className="font-medium">{rel.target_type}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-8 text-muted-foreground">
                          No relationships defined for this entity type
                        </div>
                      )}
                    </ScrollArea>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="graph">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <GitBranch className="h-5 w-5" />
                      Schema Relationship Graph
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {relationshipGraph ? (
                      <ScrollArea className="h-96">
                        <div className="space-y-6">
                          {/* Entity Nodes */}
                          <div>
                            <h4 className="font-medium mb-3">Entity Types</h4>
                            <div className="grid grid-cols-2 gap-3">
                              {relationshipGraph.nodes
                                .filter(node => node.type === 'entity')
                                .map((node) => (
                                  <div
                                    key={node.id}
                                    className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                                      selectedSchema?.entity_type === node.id
                                        ? 'border-primary bg-primary/5'
                                        : 'border-border hover:border-primary/50'
                                    }`}
                                    onClick={() => {
                                      const schema = schemas.find(s => s.entity_type === node.id);
                                      if (schema) handleSchemaSelect(schema);
                                    }}
                                  >
                                    <div className="flex items-center gap-2">
                                      <Database className="h-4 w-4 text-muted-foreground" />
                                      <span className="font-medium text-sm">{node.label}</span>
                                    </div>
                                  </div>
                                ))}
                            </div>
                          </div>

                          <Separator />

                          {/* Relationships */}
                          <div>
                            <h4 className="font-medium mb-3">Relationships</h4>
                            <div className="space-y-2">
                              {relationshipGraph.edges.map((edge, index) => (
                                <div
                                  key={index}
                                  className="flex items-center gap-3 p-3 rounded-lg border bg-muted/30"
                                >
                                  <Badge variant="outline" className="text-xs">
                                    {edge.source}
                                  </Badge>
                                  <div className="flex items-center gap-1 text-sm text-muted-foreground">
                                    <span>{edge.label}</span>
                                    <span>→</span>
                                  </div>
                                  <Badge variant="outline" className="text-xs">
                                    {edge.target}
                                  </Badge>
                                  <Badge 
                                    variant="secondary" 
                                    className={`text-xs ml-auto ${getCardinalityColor(edge.cardinality)}`}
                                  >
                                    {edge.cardinality}
                                  </Badge>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </ScrollArea>
                    ) : (
                      <div className="text-center py-8 text-muted-foreground">
                        Loading relationship graph...
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          ) : (
            <Card>
              <CardContent className="text-center py-12">
                <Eye className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium mb-2">No Schema Selected</h3>
                <p className="text-muted-foreground">
                  Select an entity type from the list to view its schema details
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}