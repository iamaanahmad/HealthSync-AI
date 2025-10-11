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
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Search, FileText } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

const QueryFormSchema = z.object({
  datasetDescription: z.string().min(20, { message: "Please provide a more detailed dataset description." }),
  researchQuestion: z.string().min(10, { message: "Please specify a clear research question." }),
});

export default function ResearcherPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [summary, setSummary] = useState<string | null>(null);
  const { toast } = useToast();

  const form = useForm<z.infer<typeof QueryFormSchema>>({
    resolver: zodResolver(QueryFormSchema),
    defaultValues: {
      datasetDescription: "Anonymized dataset of 5,000 patients with a history of cardiovascular events. Includes demographic data, cholesterol levels, blood pressure readings, and prescribed medications over a 5-year period.",
      researchQuestion: "What is the correlation between statin usage and changes in cholesterol levels in patients over 50?",
    },
  });

  const onSubmit: SubmitHandler<z.infer<typeof QueryFormSchema>> = async (data) => {
    setIsLoading(true);
    setSummary(null);
    // Placeholder for uAgent interaction
    setTimeout(() => {
        setSummary("Based on the dataset description, a strong correlation analysis is possible. The data includes the necessary variables: statin usage (from prescribed medications), cholesterol levels, and patient age. The 5-year longitudinal data will allow for tracking changes over time.");
        setIsLoading(false);
    }, 1500)
  };

  return (
    <div className="container mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
      <Card>
        <CardHeader>
          <CardTitle className="font-headline text-2xl">Researcher Query Portal</CardTitle>
          <CardDescription>
            Submit structured queries to identify and get summaries of available anonymized datasets.
          </CardDescription>
        </CardHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <CardContent className="space-y-4">
              <FormField
                control={form.control}
                name="datasetDescription"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Dataset Description</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Describe the dataset you are looking for..."
                        className="min-h-[120px]"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      Provide details about the kind of anonymized data you need.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="researchQuestion"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Research Question</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="What question are you trying to answer?"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      Your specific question will help find the most relevant data.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
            <CardFooter>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Search className="mr-2 h-4 w-4" />
                )}
                Query Datasets
              </Button>
            </CardFooter>
          </form>
        </Form>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle className="font-headline flex items-center gap-2"><FileText />Query Results</CardTitle>
          <CardDescription>
            A summary of the dataset's relevance to your research question will appear here.
          </CardDescription>
        </CardHeader>
        <CardContent className="min-h-[300px]">
          {isLoading && (
            <div className="space-y-4">
              <Skeleton className="h-4 w-4/5" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
            </div>
          )}
          {summary && !isLoading && (
            <p className="text-sm whitespace-pre-wrap leading-relaxed">
              {summary}
            </p>
          )}
          {!summary && !isLoading && (
             <div className="flex items-center justify-center h-full text-muted-foreground">
                <p>Results will be displayed here.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
