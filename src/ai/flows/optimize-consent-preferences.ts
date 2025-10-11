'use server';

/**
 * @fileOverview AI flow to suggest optimal consent preferences for patients.
 *
 * - optimizeConsentPreferences - A function that suggests consent preferences.
 * - OptimizeConsentPreferencesInput - The input type for the optimizeConsentPreferences function.
 * - OptimizeConsentPreferencesOutput - The return type for the optimizeConsentPreferences function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const OptimizeConsentPreferencesInputSchema = z.object({
  healthProfile: z
    .string()
    .describe("Patient's health profile, including medical history and current conditions."),
  researchInterests: z
    .string()
    .describe("Patient's research interests, specified as keywords or topics."),
  currentConsentPreferences: z
    .string()
    .optional()
    .describe('The current consent preferences of the patient, in JSON format.'),
});
export type OptimizeConsentPreferencesInput = z.infer<
  typeof OptimizeConsentPreferencesInputSchema
>;

const OptimizeConsentPreferencesOutputSchema = z.object({
  suggestedConsentPreferences: z
    .string()
    .describe(
      'AI-suggested consent preferences, optimized for research benefit and privacy protection, in JSON format.'
    ),
  explanation: z
    .string()
    .describe(
      'Explanation of why these consent preferences are suggested, including potential research benefits and privacy considerations.'
    ),
});
export type OptimizeConsentPreferencesOutput = z.infer<
  typeof OptimizeConsentPreferencesOutputSchema
>;

export async function optimizeConsentPreferences(
  input: OptimizeConsentPreferencesInput
): Promise<OptimizeConsentPreferencesOutput> {
  return optimizeConsentPreferencesFlow(input);
}

const prompt = ai.definePrompt({
  name: 'optimizeConsentPreferencesPrompt',
  input: {schema: OptimizeConsentPreferencesInputSchema},
  output: {schema: OptimizeConsentPreferencesOutputSchema},
  prompt: `You are an AI assistant specialized in optimizing patient consent preferences for medical research.

  Based on the patient's health profile, research interests, and current consent preferences (if any), suggest optimal consent preferences that balance research benefits and privacy protection.

  Health Profile: {{{healthProfile}}}
  Research Interests: {{{researchInterests}}}
  Current Consent Preferences: {{{currentConsentPreferences}}}

  Consider the following factors:
  - The potential for the patient's data to contribute to valuable research.
  - The patient's privacy concerns and preferences.
  - Ethical guidelines and regulations regarding data sharing.

  Provide a clear explanation of why these consent preferences are suggested, including potential research benefits and privacy considerations.

  Format the suggested consent preferences as a JSON object.
  `,
});

const optimizeConsentPreferencesFlow = ai.defineFlow(
  {
    name: 'optimizeConsentPreferencesFlow',
    inputSchema: OptimizeConsentPreferencesInputSchema,
    outputSchema: OptimizeConsentPreferencesOutputSchema,
  },
  async input => {
    const {output} = await prompt(input);
    return output!;
  }
);
