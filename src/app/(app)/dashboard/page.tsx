"use client";

import { useState } from "react";
import { useForm, type SubmitHandler } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Bot, Loader2, Sparkles } from "lucide-react";

import type {
  OptimizeConsentPreferencesInput,
  OptimizeConsentPreferencesOutput
} from "@/ai/flows/optimize-consent-preferences";
import { optimizeConsentPreferences } from "@/ai/flows/optimize-consent-preferences";
import { useToast } from "@/hooks/use-toast";

const consentOptions = [
  { id: "genomicData", label: "Genomic Data", description: "Share your full genomic sequence for research." },
  { id: "clinicalTrials", label: "Clinical Trials", description: "Be contacted for relevant clinical trials." },
  { id: "imagingData", label: "Medical Imaging", description: "Allow use of anonymized X-rays, MRIs, etc." },
  { id: "healthRecords", label: "Electronic Health Records", description: "Share anonymized EHR data for population studies." },
  { id: "wearableData", label: "Wearable Device Data", description: "Contribute data from fitness trackers and smartwatches." },
];

const OptimizeFormSchema = z.object({
  healthProfile: z.string().min(10, { message: "Please provide a brief health profile." }),
  researchInterests: z.string().min(3, { message: "Please list at least one research interest." }),
});

export default function DashboardPage() {
  const [consent, setConsent] = useState({
    genomicData: true,
    clinicalTrials: false,
    imagingData: true,
    healthRecords: true,
    wearableData: false,
  });

  const [isLoading, setIsLoading] = useState(false);
  const [aiResult, setAiResult] = useState<OptimizeConsentPreferencesOutput | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const { toast } = useToast();

  const form = useForm<z.infer<typeof OptimizeFormSchema>>({
    resolver: zodResolver(OptimizeFormSchema),
    defaultValues: { healthProfile: "", researchInterests: "" },
  });

  const handleConsentChange = (id: keyof typeof consent) => {
    setConsent((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const onSubmit: SubmitHandler<z.infer<typeof OptimizeFormSchema>> = async (data) => {
    setIsLoading(true);
    setAiResult(null);
    try {
      const input: OptimizeConsentPreferencesInput = {
        ...data,
        currentConsentPreferences: JSON.stringify(consent, null, 2),
      };
      const result = await optimizeConsentPreferences(input);
      setAiResult(result);
    } catch (error) {
      console.error("AI optimization failed:", error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to get AI suggestions. Please try again.",
      });
    } finally {
      setIsLoading(false);
    }
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
        <CardFooter>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Sparkles className="mr-2 h-4 w-4" />
                Optimize with AI
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[600px]">
              <DialogHeader>
                <DialogTitle className="font-headline flex items-center gap-2"><Bot />AI-Powered Consent Agent</DialogTitle>
                <DialogDescription>
                  Provide some details for the AI to suggest optimized consent settings for you.
                </DialogDescription>
              </DialogHeader>
              {!aiResult ? (
                 <Form {...form}>
                 <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                   <FormField
                     control={form.control}
                     name="healthProfile"
                     render={({ field }) => (
                       <FormItem>
                         <FormLabel>Health Profile</FormLabel>
                         <FormControl>
                           <Textarea placeholder="e.g., 'Diagnosed with Type 2 diabetes, managing with diet and metformin.'" {...field} />
                         </FormControl>
                         <FormDescription>Briefly describe your health status.</FormDescription>
                         <FormMessage />
                       </FormItem>
                     )}
                   />
                   <FormField
                     control={form.control}
                     name="researchInterests"
                     render={({ field }) => (
                       <FormItem>
                         <FormLabel>Research Interests</FormLabel>
                         <FormControl>
                           <Input placeholder="e.g., 'Diabetes research, genetics, longevity'" {...field} />
                         </FormControl>
                         <FormDescription>Keywords or topics you're interested in.</FormDescription>
                         <FormMessage />
                       </FormItem>
                     )}
                   />
                   <DialogFooter>
                     <Button type="submit" disabled={isLoading}>
                       {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Sparkles className="mr-2 h-4 w-4" />}
                       Get Suggestions
                     </Button>
                   </DialogFooter>
                 </form>
               </Form>
              ) : (
                <div className="space-y-4">
                  <Alert>
                    <Sparkles className="h-4 w-4" />
                    <AlertTitle className="font-headline">AI Suggestions</AlertTitle>
                    <AlertDescription>
                      {aiResult.explanation}
                    </AlertDescription>
                  </Alert>
                  <div>
                    <h4 className="font-semibold mb-2">Suggested Preferences:</h4>
                    <pre className="p-4 bg-muted rounded-md text-sm overflow-x-auto">
                      <code>{aiResult.suggestedConsentPreferences}</code>
                    </pre>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => { setAiResult(null); form.reset(); }}>
                      Start Over
                    </Button>
                     <Button onClick={() => setDialogOpen(false)}>Done</Button>
                  </DialogFooter>
                </div>
              )}
            </DialogContent>
          </Dialog>
        </CardFooter>
      </Card>
    </div>
  );
}
