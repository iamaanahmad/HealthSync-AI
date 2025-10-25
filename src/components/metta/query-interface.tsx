"use client";

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { 
  Play, 
  Save, 
  History, 
  FileText, 
  CheckCircle, 
  XCircle, 
  Clock,
  Code,
  Lightbulb
} from "lucide-react";
import { mettaAPI, MeTTaQuery, MeTTaResponse, QueryTemplate } from "@/lib/metta-api";
import { useToast } from "@/hooks/use-toast";

interface QueryInterfaceProps {
  onQueryExecuted: (response: MeTTaResponse) => void;
}

interface QueryHistory {
  id: string;
  query: MeTTaQuery;
  response: MeTTaResponse;
  timestamp: Date;
}

export function QueryInterface({ onQueryExecuted }: QueryInterfaceProps) {
  const [query, setQuery] = useState('');
  const [queryType, setQueryType] = useState('');
  const [contextVariables, setContextVariables] = useState<Record<string, string>>({});
  const [templates, setTemplates] = useState<QueryTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<QueryTemplate | null>(null);
  const [queryHistory, setQueryHistory] = useState<QueryHistory[]>([]);
  const [isExecuting, setIsExecuting] = useState(false);
  const [validationResult, setValidationResult] = useState<{ valid: boolean; errors?: string[] } | null>(null);
  const [currentResponse, setCurrentResponse] = useState<MeTTaResponse | null>(null);
  const { toast } = useToast();

  const loadTemplates = useCallback(async () => {
    try {
      const templatesData = await mettaAPI.getQueryTemplates();
      setTemplates(templatesData);
    } catch (error) {
      console.error('Failed to load query templates:', error);
      toast({
        title: "Error",
        description: "Failed to load query templates",
        variant: "destructive",
      });
    }
  }, [toast]);

  const validateQuery = useCallback(async (queryText: string) => {
    if (!queryText.trim()) {
      setValidationResult(null);
      return;
    }

    try {
      const result = await mettaAPI.validateQuery(queryText);
      setValidationResult(result);
    } catch (error) {
      console.error('Query validation failed:', error);
      setValidationResult({ valid: false, errors: ['Validation service unavailable'] });
    }
  }, []);

  const executeQuery = async () => {
    if (!query.trim()) {
      toast({
        title: "Error",
        description: "Please enter a query",
        variant: "destructive",
      });
      return;
    }

    if (validationResult && !validationResult.valid) {
      toast({
        title: "Error",
        description: "Please fix query errors before executing",
        variant: "destructive",
      });
      return;
    }

    setIsExecuting(true);
    
    try {
      const queryObj: MeTTaQuery = {
        query_type: queryType || 'custom',
        query_expression: query,
        context_variables: contextVariables,
      };

      const response = await mettaAPI.executeQuery(queryObj);
      
      // Add to history
      const historyEntry: QueryHistory = {
        id: response.query_id,
        query: queryObj,
        response,
        timestamp: new Date(),
      };
      
      setQueryHistory(prev => [historyEntry, ...prev.slice(0, 9)]); // Keep last 10
      setCurrentResponse(response);
      onQueryExecuted(response);

      toast({
        title: "Query Executed",
        description: `Query completed with confidence score: ${response.confidence_score}`,
      });
    } catch (error) {
      console.error('Query execution failed:', error);
      toast({
        title: "Error",
        description: "Failed to execute query",
        variant: "destructive",
      });
    } finally {
      setIsExecuting(false);
    }
  };

  const loadTemplate = (template: QueryTemplate) => {
    setSelectedTemplate(template);
    setQuery(template.template);
    setQueryType(template.query_type);
    
    // Initialize context variables with example values
    const newContextVars: Record<string, string> = {};
    template.parameters.forEach(param => {
      if (template.example_values && template.example_values[param.name]) {
        newContextVars[param.name] = String(template.example_values[param.name]);
      } else {
        newContextVars[param.name] = '';
      }
    });
    setContextVariables(newContextVars);
  };

  const loadFromHistory = (historyEntry: QueryHistory) => {
    setQuery(historyEntry.query.query_expression);
    setQueryType(historyEntry.query.query_type);
    setContextVariables(historyEntry.query.context_variables || {});
    setCurrentResponse(historyEntry.response);
  };

  const updateContextVariable = (key: string, value: string) => {
    setContextVariables(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const substituteVariables = (template: string, variables: Record<string, string>): string => {
    let result = template;
    Object.entries(variables).forEach(([key, value]) => {
      result = result.replace(new RegExp(`\\$\\{${key}\\}`, 'g'), value);
    });
    return result;
  };

  useEffect(() => {
    loadTemplates();
  }, [loadTemplates]);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      validateQuery(query);
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [query, validateQuery]);

  // Update query when context variables change for templates
  useEffect(() => {
    if (selectedTemplate && Object.keys(contextVariables).length > 0) {
      const substituted = substituteVariables(selectedTemplate.template, contextVariables);
      setQuery(substituted);
    }
  }, [contextVariables, selectedTemplate]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Query Editor */}
      <div className="lg:col-span-2 space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Code className="h-5 w-5" />
              Query Editor
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Select value={queryType} onValueChange={setQueryType}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Query type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="has_valid_consent">Check Consent</SelectItem>
                  <SelectItem value="get_privacy_rule">Get Privacy Rule</SelectItem>
                  <SelectItem value="validate_research_request">Validate Research</SelectItem>
                  <SelectItem value="find_consenting_patients">Find Patients</SelectItem>
                  <SelectItem value="traverse_consent_chain">Traverse Consent</SelectItem>
                  <SelectItem value="custom">Custom Query</SelectItem>
                </SelectContent>
              </Select>
              
              <Button 
                variant="outline" 
                onClick={executeQuery}
                disabled={isExecuting || (validationResult && !validationResult.valid)}
                className="flex items-center gap-2"
              >
                {isExecuting ? (
                  <Clock className="h-4 w-4 animate-spin" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
                Execute Query
              </Button>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="query">MeTTa Query Expression</Label>
                {validationResult && (
                  <div className="flex items-center gap-1">
                    {validationResult.valid ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                    <span className={`text-sm ${validationResult.valid ? 'text-green-600' : 'text-red-600'}`}>
                      {validationResult.valid ? 'Valid' : 'Invalid'}
                    </span>
                  </div>
                )}
              </div>
              
              <Textarea
                id="query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter your MeTTa query expression..."
                className="font-mono text-sm min-h-32"
              />
              
              {validationResult && !validationResult.valid && validationResult.errors && (
                <div className="text-sm text-red-600 space-y-1">
                  {validationResult.errors.map((error, index) => (
                    <div key={index}>• {error}</div>
                  ))}
                </div>
              )}
            </div>

            {/* Context Variables */}
            {selectedTemplate && selectedTemplate.parameters.length > 0 && (
              <div className="space-y-3">
                <Label>Parameters</Label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {selectedTemplate.parameters.map((param) => (
                    <div key={param.name} className="space-y-1">
                      <Label htmlFor={param.name} className="text-sm">
                        {param.name}
                        {param.required && <span className="text-red-500 ml-1">*</span>}
                      </Label>
                      <Input
                        id={param.name}
                        value={contextVariables[param.name] || ''}
                        onChange={(e) => updateContextVariable(param.name, e.target.value)}
                        placeholder={param.description}
                        className="text-sm"
                      />
                      {param.description && (
                        <div className="text-xs text-muted-foreground">{param.description}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Query Results */}
        {currentResponse && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5" />
                Query Results
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4">
                <Badge variant={currentResponse.confidence_score >= 0.8 ? "default" : "secondary"}>
                  Confidence: {(currentResponse.confidence_score * 100).toFixed(1)}%
                </Badge>
                <Badge variant="outline">
                  Results: {currentResponse.results.length}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  Query ID: {currentResponse.query_id}
                </span>
              </div>

              {currentResponse.results.length > 0 && (
                <div className="space-y-2">
                  <Label>Results</Label>
                  <ScrollArea className="h-48 border rounded-md p-3">
                    <pre className="text-sm font-mono">
                      {JSON.stringify(currentResponse.results, null, 2)}
                    </pre>
                  </ScrollArea>
                </div>
              )}

              {currentResponse.reasoning_path.length > 0 && (
                <div className="space-y-2">
                  <Label>Reasoning Path</Label>
                  <ScrollArea className="h-32 border rounded-md p-3">
                    <div className="space-y-1">
                      {currentResponse.reasoning_path.map((step, index) => (
                        <div key={index} className="text-sm flex gap-2">
                          <span className="text-muted-foreground min-w-6">{index + 1}.</span>
                          <span>{step}</span>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Templates and History */}
      <div className="space-y-4">
        {/* Query Templates */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileTemplate className="h-5 w-5" />
              Query Templates
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-64">
              <div className="space-y-2">
                {templates.map((template) => (
                  <div
                    key={template.id}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedTemplate?.id === template.id
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:border-primary/50 hover:bg-muted/50'
                    }`}
                    onClick={() => loadTemplate(template)}
                  >
                    <div className="font-medium text-sm">{template.name}</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      {template.description}
                    </div>
                    <Badge variant="outline" className="mt-2 text-xs">
                      {template.query_type}
                    </Badge>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Query History */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <History className="h-5 w-5" />
              Query History
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-64">
              {queryHistory.length > 0 ? (
                <div className="space-y-2">
                  {queryHistory.map((entry) => (
                    <div
                      key={entry.id}
                      className="p-3 rounded-lg border cursor-pointer hover:border-primary/50 hover:bg-muted/50 transition-colors"
                      onClick={() => loadFromHistory(entry)}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <Badge variant="outline" className="text-xs">
                          {entry.query.query_type}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {entry.timestamp.toLocaleTimeString()}
                        </span>
                      </div>
                      <div className="text-sm font-mono truncate">
                        {entry.query.query_expression}
                      </div>
                      <div className="flex items-center gap-2 mt-2">
                        <Badge 
                          variant={entry.response.confidence_score >= 0.8 ? "default" : "secondary"}
                          className="text-xs"
                        >
                          {(entry.response.confidence_score * 100).toFixed(0)}%
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {entry.response.results.length} results
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground text-sm">
                  No query history yet
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Query Tips */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5" />
              Query Tips
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm space-y-2">
            <div>• Use templates for common query patterns</div>
            <div>• Variables are substituted with ${'{variable_name}'}</div>
            <div>• Check validation status before executing</div>
            <div>• Review reasoning paths to understand results</div>
            <div>• Higher confidence scores indicate more reliable results</div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}