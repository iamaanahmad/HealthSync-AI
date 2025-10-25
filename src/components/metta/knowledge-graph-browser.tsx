"use client";

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { 
  Search, 
  Filter, 
  RefreshCw, 
  Network, 
  Database,
  Users,
  FileText,
  Shield,
  Settings
} from "lucide-react";
import { mettaAPI, KnowledgeGraphStats } from "@/lib/metta-api";
import { useToast } from "@/hooks/use-toast";

interface KnowledgeGraphBrowserProps {
  onEntitySelected: (entityType: string, entityId: string) => void;
  selectedEntity?: string | null;
}

interface EntityNode {
  id: string;
  type: string;
  label: string;
  properties: Record<string, any>;
  relationships: Array<{
    target: string;
    type: string;
    label: string;
  }>;
}

const entityTypeIcons: Record<string, any> = {
  'Patient': Users,
  'ConsentRecord': FileText,
  'DataType': Database,
  'ResearchCategory': Network,
  'PrivacyRule': Shield,
  'AnonymizationMethod': Settings,
};

const entityTypeColors: Record<string, string> = {
  'Patient': 'bg-blue-100 text-blue-800 border-blue-200',
  'ConsentRecord': 'bg-green-100 text-green-800 border-green-200',
  'DataType': 'bg-purple-100 text-purple-800 border-purple-200',
  'ResearchCategory': 'bg-orange-100 text-orange-800 border-orange-200',
  'PrivacyRule': 'bg-red-100 text-red-800 border-red-200',
  'AnonymizationMethod': 'bg-yellow-100 text-yellow-800 border-yellow-200',
};

export function KnowledgeGraphBrowser({ onEntitySelected, selectedEntity }: KnowledgeGraphBrowserProps) {
  const [stats, setStats] = useState<KnowledgeGraphStats | null>(null);
  const [entities, setEntities] = useState<Record<string, Array<Record<string, any>>>>({});
  const [selectedEntityType, setSelectedEntityType] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedEntityDetails, setSelectedEntityDetails] = useState<EntityNode | null>(null);
  const { toast } = useToast();

  const loadStats = useCallback(async () => {
    try {
      setLoading(true);
      const statsData = await mettaAPI.getKnowledgeGraphStats();
      setStats(statsData);
      
      // Load entities for the first entity type
      const firstEntityType = Object.keys(statsData.entities_by_type)[0];
      if (firstEntityType) {
        setSelectedEntityType(firstEntityType);
        await loadEntitiesForType(firstEntityType);
      }
    } catch (error) {
      console.error('Failed to load knowledge graph stats:', error);
      toast({
        title: "Error",
        description: "Failed to load knowledge graph statistics",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  const loadEntitiesForType = async (entityType: string) => {
    try {
      const entitiesData = await mettaAPI.getEntitiesByType(entityType);
      setEntities(prev => ({
        ...prev,
        [entityType]: entitiesData
      }));
    } catch (error) {
      console.error(`Failed to load entities for type ${entityType}:`, error);
      toast({
        title: "Error",
        description: `Failed to load ${entityType} entities`,
        variant: "destructive",
      });
    }
  };

  const handleEntityTypeChange = async (entityType: string) => {
    setSelectedEntityType(entityType);
    setSelectedEntityDetails(null);
    
    if (!entities[entityType]) {
      await loadEntitiesForType(entityType);
    }
  };

  const handleEntityClick = (entity: Record<string, any>) => {
    const entityId = getEntityId(entity, selectedEntityType);
    
    // Create detailed entity node
    const entityNode: EntityNode = {
      id: entityId,
      type: selectedEntityType,
      label: getEntityLabel(entity, selectedEntityType),
      properties: entity,
      relationships: generateMockRelationships(entityId, selectedEntityType)
    };
    
    setSelectedEntityDetails(entityNode);
    onEntitySelected(selectedEntityType, entityId);
  };

  const getEntityId = (entity: Record<string, any>, entityType: string): string => {
    const idFields: Record<string, string> = {
      'Patient': 'patient_id',
      'ConsentRecord': 'consent_id',
      'DataType': 'type_id',
      'ResearchCategory': 'category_id',
      'PrivacyRule': 'rule_id',
      'AnonymizationMethod': 'method_id',
    };
    
    return entity[idFields[entityType]] || 'unknown';
  };

  const getEntityLabel = (entity: Record<string, any>, entityType: string): string => {
    const labelFields: Record<string, string> = {
      'Patient': 'patient_id',
      'ConsentRecord': 'consent_id',
      'DataType': 'type_name',
      'ResearchCategory': 'category_name',
      'PrivacyRule': 'rule_name',
      'AnonymizationMethod': 'method_name',
    };
    
    const field = labelFields[entityType];
    return entity[field] || entity[Object.keys(entity)[0]] || 'Unknown';
  };

  const generateMockRelationships = (entityId: string, entityType: string) => {
    // Generate mock relationships based on entity type
    const relationships: Array<{ target: string; type: string; label: string }> = [];
    
    switch (entityType) {
      case 'Patient':
        relationships.push(
          { target: 'C001', type: 'ConsentRecord', label: 'has_consent' },
          { target: 'C002', type: 'ConsentRecord', label: 'has_consent' }
        );
        break;
      case 'ConsentRecord':
        relationships.push(
          { target: 'P001', type: 'Patient', label: 'belongs_to' },
          { target: 'DT001', type: 'DataType', label: 'covers' },
          { target: 'RC001', type: 'ResearchCategory', label: 'allows' }
        );
        break;
      case 'DataType':
        relationships.push(
          { target: 'PR001', type: 'PrivacyRule', label: 'governed_by' }
        );
        break;
    }
    
    return relationships;
  };

  const filteredEntities = selectedEntityType && entities[selectedEntityType] 
    ? entities[selectedEntityType].filter(entity => {
        if (!searchTerm) return true;
        const label = getEntityLabel(entity, selectedEntityType).toLowerCase();
        const id = getEntityId(entity, selectedEntityType).toLowerCase();
        return label.includes(searchTerm.toLowerCase()) || id.includes(searchTerm.toLowerCase());
      })
    : [];

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Statistics Overview */}
      <div className="lg:col-span-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Network className="h-5 w-5" />
                Knowledge Graph Overview
              </CardTitle>
            </div>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={loadStats}
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </CardHeader>
          <CardContent>
            {stats ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary">{stats.total_entities}</div>
                  <div className="text-sm text-muted-foreground">Total Entities</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary">{stats.total_relationships}</div>
                  <div className="text-sm text-muted-foreground">Relationships</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary">
                    {Object.keys(stats.entities_by_type).length}
                  </div>
                  <div className="text-sm text-muted-foreground">Entity Types</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary">
                    {Math.round((stats.total_relationships / stats.total_entities) * 100) / 100}
                  </div>
                  <div className="text-sm text-muted-foreground">Avg Relations</div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                Loading statistics...
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Entity Browser */}
      <div className="lg:col-span-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              Entity Browser
            </CardTitle>
            <div className="flex gap-2">
              <Select value={selectedEntityType} onValueChange={handleEntityTypeChange}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Select entity type" />
                </SelectTrigger>
                <SelectContent>
                  {stats && Object.entries(stats.entities_by_type).map(([type, count]) => {
                    const Icon = entityTypeIcons[type] || Database;
                    return (
                      <SelectItem key={type} value={type}>
                        <div className="flex items-center gap-2">
                          <Icon className="h-4 w-4" />
                          {type} ({count})
                        </div>
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
              
              <div className="relative flex-1">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search entities..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-96">
              {filteredEntities.length > 0 ? (
                <div className="space-y-2">
                  {filteredEntities.map((entity, index) => {
                    const entityId = getEntityId(entity, selectedEntityType);
                    const label = getEntityLabel(entity, selectedEntityType);
                    const Icon = entityTypeIcons[selectedEntityType] || Database;
                    const isSelected = selectedEntity === `${selectedEntityType}:${entityId}`;
                    
                    return (
                      <div
                        key={index}
                        className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                          isSelected 
                            ? 'border-primary bg-primary/5' 
                            : 'border-border hover:border-primary/50 hover:bg-muted/50'
                        }`}
                        onClick={() => handleEntityClick(entity)}
                      >
                        <div className="flex items-center gap-3">
                          <Icon className="h-4 w-4 text-muted-foreground" />
                          <div className="flex-1 min-w-0">
                            <div className="font-medium truncate">{label}</div>
                            <div className="text-sm text-muted-foreground">ID: {entityId}</div>
                          </div>
                          <Badge 
                            variant="outline" 
                            className={entityTypeColors[selectedEntityType] || 'bg-gray-100 text-gray-800'}
                          >
                            {selectedEntityType}
                          </Badge>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  {selectedEntityType ? 'No entities found' : 'Select an entity type to browse'}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {/* Entity Details */}
      <div>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Entity Details
            </CardTitle>
          </CardHeader>
          <CardContent>
            {selectedEntityDetails ? (
              <div className="space-y-4">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    {(() => {
                      const Icon = entityTypeIcons[selectedEntityDetails.type] || Database;
                      return <Icon className="h-4 w-4" />;
                    })()}
                    <span className="font-medium">{selectedEntityDetails.label}</span>
                    <Badge 
                      variant="outline"
                      className={entityTypeColors[selectedEntityDetails.type] || 'bg-gray-100 text-gray-800'}
                    >
                      {selectedEntityDetails.type}
                    </Badge>
                  </div>
                  <div className="text-sm text-muted-foreground">ID: {selectedEntityDetails.id}</div>
                </div>

                <Separator />

                <div>
                  <h4 className="font-medium mb-2">Properties</h4>
                  <div className="space-y-2">
                    {Object.entries(selectedEntityDetails.properties).map(([key, value]) => (
                      <div key={key} className="flex justify-between text-sm">
                        <span className="text-muted-foreground">{key}:</span>
                        <span className="font-mono text-right max-w-32 truncate">
                          {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {selectedEntityDetails.relationships.length > 0 && (
                  <>
                    <Separator />
                    <div>
                      <h4 className="font-medium mb-2">Relationships</h4>
                      <div className="space-y-2">
                        {selectedEntityDetails.relationships.map((rel, index) => (
                          <div key={index} className="flex items-center gap-2 text-sm">
                            <Badge variant="secondary" className="text-xs">
                              {rel.label}
                            </Badge>
                            <span className="text-muted-foreground">→</span>
                            <span>{rel.target}</span>
                            <span className="text-muted-foreground">({rel.type})</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                Select an entity to view details
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}