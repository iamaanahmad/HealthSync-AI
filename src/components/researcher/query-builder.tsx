"use client";

import { useState, useEffect } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { CalendarIcon, Plus, Trash2, AlertCircle, CheckCircle, Clock, FileText } from 'lucide-react';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';
import { 
  ResearchQuery, 
  ResearchQuerySchema, 
  QueryTemplate,
  AVAILABLE_DATA_TYPES, 
  RESEARCH_CATEGORIES,
  ResearchQueryService 
} from '@/lib/research-query-api';

interface QueryBuilderProps {
  onQuerySubmit: (queryId: string) => void;
  templates?: QueryTemplate[];
}

export function QueryBuilder({ onQuerySubmit, templates = [] }: QueryBuilderProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitProgress, setSubmitProgress] = useState(0);
  const [selectedTemplate, setSelectedTemplate] = useState<QueryTemplate | null>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  const form = useForm<ResearchQuery>({
    resolver: zodResolver(ResearchQuerySchema),
    defaultValues: {
      researcherId: ResearchQueryService.getCurrentResearcher().researcherId,
      studyTitle: '',
      studyDescription: '',
      dataRequirements: {
        dataTypes: [],
        researchCategories: [],
        minimumSampleSize: 100,
        dataRetentionDays: 365,
      },
      inclusionCriteria: [],
      exclusionCriteria: [],
      ethicalApprovalId: '',
      privacyRequirements: {
        anonymizationMethods: ['k_anonymity'],
        enhancedAnonymization: false,
      },
    },
  });

  const { fields: inclusionFields, append: appendInclusion, remove: removeInclusion } = useFieldArray({
    control: form.control,
    name: 'inclusionCriteria',
  });

  const { fields: exclusionFields, append: appendExclusion, remove: removeExclusion } = useFieldArray({
    control: form.control,
    name: 'exclusionCriteria',
  });

  // Load template into form
  const loadTemplate = (template: QueryTemplate) => {
    setSelectedTemplate(template);
    form.reset({
      ...form.getValues(),
      studyTitle: template.template.studyTitle,
      studyDescription: template.template.studyDescription,
      dataRequirements: {
        ...form.getValues().dataRequirements,
        dataTypes: template.template.dataRequirements.dataTypes,
        researchCategories: template.template.dataRequirements.researchCategories,
        minimumSampleSize: template.template.dataRequirements.minimumSampleSize || 100,
      },
      inclusionCriteria: template.template.inclusionCriteria || [],
      exclusionCriteria: template.template.exclusionCriteria || [],
    });
  };

  // Real-time validation
  useEffect(() => {
    const subscription = form.watch((value) => {
      try {
        ResearchQuerySchema.parse(value);
        setValidationErrors([]);
      } catch (error: any) {
        if (error.errors) {
          setValidationErrors(error.errors.map((e: any) => e.message));
        }
      }
    });
    return () => subscription.unsubscribe();
  }, [form]);

  const onSubmit = async (data: ResearchQuery) => {
    setIsSubmitting(true);
    setSubmitProgress(0);

    // Simulate progress updates
    const progressInterval = setInterval(() => {
      setSubmitProgress(prev => Math.min(prev + 10, 90));
    }, 200);

    try {
      const result = await ResearchQueryService.submitQuery(data);
      
      clearInterval(progressInterval);
      setSubmitProgress(100);

      if (result.success && result.queryId) {
        setTimeout(() => {
          onQuerySubmit(result.queryId!);
          form.reset();
          setSelectedTemplate(null);
        }, 500);
      } else {
        throw new Error(result.error || 'Failed to submit query');
      }
    } catch (error) {
      clearInterval(progressInterval);
      setSubmitProgress(0);
      console.error('Query submission failed:', error);
    } finally {
      setTimeout(() => setIsSubmitting(false), 500);
    }
  };

  return (
    <div className="space-y-6">
      {/* Template Selection */}
      {templates.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Query Templates
            </CardTitle>
            <CardDescription>
              Start with a pre-built template for common research patterns
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {templates.map((template) => (
                <Card 
                  key={template.templateId} 
                  className={cn(
                    "cursor-pointer transition-colors hover:bg-muted/50",
                    selectedTemplate?.templateId === template.templateId && "ring-2 ring-primary"
                  )}
                  onClick={() => loadTemplate(template)}
                >
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">{template.name}</CardTitle>
                    <Badge variant="secondary" className="w-fit text-xs">
                      {template.category}
                    </Badge>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <p className="text-xs text-muted-foreground">{template.description}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Query Builder Form */}
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <Tabs defaultValue="basic" className="space-y-6">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="basic">Basic Info</TabsTrigger>
              <TabsTrigger value="data">Data Requirements</TabsTrigger>
              <TabsTrigger value="criteria">Criteria</TabsTrigger>
              <TabsTrigger value="compliance">Compliance</TabsTrigger>
            </TabsList>

            {/* Basic Information */}
            <TabsContent value="basic" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Study Information</CardTitle>
                  <CardDescription>
                    Provide basic information about your research study
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <FormField
                    control={form.control}
                    name="researcherId"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Researcher ID</FormLabel>
                        <FormControl>
                          <Input {...field} disabled />
                        </FormControl>
                        <FormDescription>
                          Your institutional researcher identifier
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="studyTitle"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Study Title</FormLabel>
                        <FormControl>
                          <Input {...field} placeholder="Enter your study title" />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="studyDescription"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Study Description</FormLabel>
                        <FormControl>
                          <Textarea 
                            {...field} 
                            placeholder="Provide a detailed description of your research study, including objectives, methodology, and expected outcomes..."
                            className="min-h-[120px]"
                          />
                        </FormControl>
                        <FormDescription>
                          Minimum 50 characters. Include research objectives, methodology, and expected outcomes.
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="studyDurationDays"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Study Duration (Days)</FormLabel>
                        <FormControl>
                          <Input 
                            {...field} 
                            type="number" 
                            placeholder="365"
                            onChange={(e) => field.onChange(e.target.value ? parseInt(e.target.value) : undefined)}
                          />
                        </FormControl>
                        <FormDescription>
                          Expected duration of the study in days
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </CardContent>
              </Card>
            </TabsContent>

            {/* Data Requirements */}
            <TabsContent value="data" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Data Types</CardTitle>
                  <CardDescription>
                    Select the types of healthcare data you need for your research
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <FormField
                    control={form.control}
                    name="dataRequirements.dataTypes"
                    render={() => (
                      <FormItem>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {AVAILABLE_DATA_TYPES.map((dataType) => (
                            <FormField
                              key={dataType.value}
                              control={form.control}
                              name="dataRequirements.dataTypes"
                              render={({ field }) => (
                                <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                                  <FormControl>
                                    <Checkbox
                                      checked={field.value?.includes(dataType.value)}
                                      onCheckedChange={(checked) => {
                                        return checked
                                          ? field.onChange([...field.value, dataType.value])
                                          : field.onChange(field.value?.filter((value) => value !== dataType.value))
                                      }}
                                    />
                                  </FormControl>
                                  <div className="space-y-1 leading-none">
                                    <FormLabel className="text-sm font-medium">
                                      {dataType.label}
                                    </FormLabel>
                                    <p className="text-xs text-muted-foreground">
                                      {dataType.description}
                                    </p>
                                  </div>
                                </FormItem>
                              )}
                            />
                          ))}
                        </div>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Research Categories</CardTitle>
                  <CardDescription>
                    Select the research categories that best describe your study
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <FormField
                    control={form.control}
                    name="dataRequirements.researchCategories"
                    render={() => (
                      <FormItem>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {RESEARCH_CATEGORIES.map((category) => (
                            <FormField
                              key={category.value}
                              control={form.control}
                              name="dataRequirements.researchCategories"
                              render={({ field }) => (
                                <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                                  <FormControl>
                                    <Checkbox
                                      checked={field.value?.includes(category.value)}
                                      onCheckedChange={(checked) => {
                                        return checked
                                          ? field.onChange([...field.value, category.value])
                                          : field.onChange(field.value?.filter((value) => value !== category.value))
                                      }}
                                    />
                                  </FormControl>
                                  <div className="space-y-1 leading-none">
                                    <FormLabel className="text-sm font-medium">
                                      {category.label}
                                    </FormLabel>
                                    <p className="text-xs text-muted-foreground">
                                      {category.description}
                                    </p>
                                  </div>
                                </FormItem>
                              )}
                            />
                          ))}
                        </div>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Sample Size & Data Range</CardTitle>
                  <CardDescription>
                    Specify your sample size requirements and data collection period
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <FormField
                    control={form.control}
                    name="dataRequirements.minimumSampleSize"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Minimum Sample Size</FormLabel>
                        <FormControl>
                          <Input 
                            {...field} 
                            type="number" 
                            placeholder="100"
                            onChange={(e) => field.onChange(e.target.value ? parseInt(e.target.value) : undefined)}
                          />
                        </FormControl>
                        <FormDescription>
                          Minimum number of patient records needed for your study
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <FormField
                      control={form.control}
                      name="dataRequirements.dateRange.startDate"
                      render={({ field }) => (
                        <FormItem className="flex flex-col">
                          <FormLabel>Start Date</FormLabel>
                          <Popover>
                            <PopoverTrigger asChild>
                              <FormControl>
                                <Button
                                  variant="outline"
                                  className={cn(
                                    "w-full pl-3 text-left font-normal",
                                    !field.value && "text-muted-foreground"
                                  )}
                                >
                                  {field.value ? (
                                    format(new Date(field.value), "PPP")
                                  ) : (
                                    <span>Pick a date</span>
                                  )}
                                  <CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
                                </Button>
                              </FormControl>
                            </PopoverTrigger>
                            <PopoverContent className="w-auto p-0" align="start">
                              <Calendar
                                mode="single"
                                selected={field.value ? new Date(field.value) : undefined}
                                onSelect={(date) => field.onChange(date?.toISOString())}
                                disabled={(date) => date > new Date()}
                                initialFocus
                              />
                            </PopoverContent>
                          </Popover>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="dataRequirements.dateRange.endDate"
                      render={({ field }) => (
                        <FormItem className="flex flex-col">
                          <FormLabel>End Date</FormLabel>
                          <Popover>
                            <PopoverTrigger asChild>
                              <FormControl>
                                <Button
                                  variant="outline"
                                  className={cn(
                                    "w-full pl-3 text-left font-normal",
                                    !field.value && "text-muted-foreground"
                                  )}
                                >
                                  {field.value ? (
                                    format(new Date(field.value), "PPP")
                                  ) : (
                                    <span>Pick a date</span>
                                  )}
                                  <CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
                                </Button>
                              </FormControl>
                            </PopoverTrigger>
                            <PopoverContent className="w-auto p-0" align="start">
                              <Calendar
                                mode="single"
                                selected={field.value ? new Date(field.value) : undefined}
                                onSelect={(date) => field.onChange(date?.toISOString())}
                                disabled={(date) => date > new Date()}
                                initialFocus
                              />
                            </PopoverContent>
                          </Popover>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Inclusion/Exclusion Criteria */}
            <TabsContent value="criteria" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Inclusion Criteria</CardTitle>
                  <CardDescription>
                    Define criteria for including patients in your study
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {inclusionFields.map((field, index) => (
                    <div key={field.id} className="flex gap-2">
                      <FormField
                        control={form.control}
                        name={`inclusionCriteria.${index}`}
                        render={({ field }) => (
                          <FormItem className="flex-1">
                            <FormControl>
                              <Input {...field} placeholder="e.g., Age 18-65 years" />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <Button
                        type="button"
                        variant="outline"
                        size="icon"
                        onClick={() => removeInclusion(index)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => appendInclusion('')}
                    className="w-full"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Inclusion Criterion
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Exclusion Criteria</CardTitle>
                  <CardDescription>
                    Define criteria for excluding patients from your study
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {exclusionFields.map((field, index) => (
                    <div key={field.id} className="flex gap-2">
                      <FormField
                        control={form.control}
                        name={`exclusionCriteria.${index}`}
                        render={({ field }) => (
                          <FormItem className="flex-1">
                            <FormControl>
                              <Input {...field} placeholder="e.g., Pregnancy" />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <Button
                        type="button"
                        variant="outline"
                        size="icon"
                        onClick={() => removeExclusion(index)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => appendExclusion('')}
                    className="w-full"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Exclusion Criterion
                  </Button>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Compliance & Privacy */}
            <TabsContent value="compliance" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Ethical Approval</CardTitle>
                  <CardDescription>
                    Provide your institutional ethical approval information
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <FormField
                    control={form.control}
                    name="ethicalApprovalId"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Ethical Approval ID</FormLabel>
                        <FormControl>
                          <Input {...field} placeholder="IRB-2024-123456" />
                        </FormControl>
                        <FormDescription>
                          Format: IRB-YYYY-NNNNNN, REB-YYYY-NNNNNN, or EC-YYYY-NNNNNN
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Privacy Requirements</CardTitle>
                  <CardDescription>
                    Specify privacy and anonymization requirements for your data
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <FormField
                    control={form.control}
                    name="privacyRequirements.enhancedAnonymization"
                    render={({ field }) => (
                      <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                        <div className="space-y-0.5">
                          <FormLabel className="text-base">Enhanced Anonymization</FormLabel>
                          <FormDescription>
                            Apply additional anonymization for sensitive data combinations
                          </FormDescription>
                        </div>
                        <FormControl>
                          <Checkbox
                            checked={field.value}
                            onCheckedChange={field.onChange}
                          />
                        </FormControl>
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="dataRequirements.dataRetentionDays"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Data Retention Period (Days)</FormLabel>
                        <FormControl>
                          <Input 
                            {...field} 
                            type="number" 
                            placeholder="365"
                            onChange={(e) => field.onChange(e.target.value ? parseInt(e.target.value) : undefined)}
                          />
                        </FormControl>
                        <FormDescription>
                          Maximum 2555 days (7 years). Data will be automatically deleted after this period.
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* Validation Status */}
          {validationErrors.length > 0 && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                <div className="space-y-1">
                  <p className="font-medium">Please fix the following issues:</p>
                  <ul className="list-disc list-inside space-y-1">
                    {validationErrors.map((error, index) => (
                      <li key={index} className="text-sm">{error}</li>
                    ))}
                  </ul>
                </div>
              </AlertDescription>
            </Alert>
          )}

          {/* Submit Button */}
          <Card>
            <CardContent className="pt-6">
              {isSubmitting && (
                <div className="space-y-2 mb-4">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    <span className="text-sm">Submitting query...</span>
                  </div>
                  <Progress value={submitProgress} className="w-full" />
                </div>
              )}
              
              <Button 
                type="submit" 
                className="w-full" 
                disabled={isSubmitting || validationErrors.length > 0}
              >
                {isSubmitting ? (
                  <>
                    <Clock className="mr-2 h-4 w-4 animate-spin" />
                    Submitting Query...
                  </>
                ) : (
                  <>
                    <CheckCircle className="mr-2 h-4 w-4" />
                    Submit Research Query
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </form>
      </Form>
    </div>
  );
}