'use server';

/**
 * @fileOverview Summarizes anonymized research datasets for researchers.
 *
 * - summarizeResearchData - A function that summarizes research data.
 * - SummarizeResearchDataInput - The input type for the summarizeResearchData function.
 * - SummarizeResearchDataOutput - The return type for the summarizeResearchData function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const SummarizeResearchDataInputSchema = z.object({
  datasetDescription: z
    .string()
    .describe('Description of the anonymized dataset to summarize.'),
  researchQuestion: z
    .string()
    .describe('The research question the researcher is trying to answer.'),
});
export type SummarizeResearchDataInput = z.infer<typeof SummarizeResearchDataInputSchema>;

const SummarizeResearchDataOutputSchema = z.object({
  summary: z
    .string()
    .describe('A summary of the anonymized dataset, focused on its suitability for the research question.'),
});
export type SummarizeResearchDataOutput = z.infer<typeof SummarizeResearchDataOutputSchema>;

export async function summarizeResearchData(
  input: SummarizeResearchDataInput
): Promise<SummarizeResearchDataOutput> {
  return summarizeResearchDataFlow(input);
}

const prompt = ai.definePrompt({
  name: 'summarizeResearchDataPrompt',
  input: {schema: SummarizeResearchDataInputSchema},
  output: {schema: SummarizeResearchDataOutputSchema},
  prompt: `You are an AI assistant helping researchers quickly assess datasets.

A researcher is trying to answer the following research question: {{{researchQuestion}}}

You have access to an anonymized dataset described as follows:
{{{datasetDescription}}}

Provide a concise summary of the dataset, highlighting its relevance and suitability for addressing the research question. Focus on key aspects and potential limitations.
`,
});

const summarizeResearchDataFlow = ai.defineFlow(
  {
    name: 'summarizeResearchDataFlow',
    inputSchema: SummarizeResearchDataInputSchema,
    outputSchema: SummarizeResearchDataOutputSchema,
  },
  async input => {
    const {output} = await prompt(input);
    return output!;
  }
);
