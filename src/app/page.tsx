import Image from "next/image";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { PlaceHolderImages } from "@/lib/placeholder-images";
import { ArrowRight } from "lucide-react";

export default function Home() {
  const heroImage = PlaceHolderImages.find((img) => img.id === "hero");

  return (
    <div className="flex flex-col min-h-screen">
      <main className="flex-1">
        <section className="relative w-full h-[60vh] md:h-[80vh] flex items-center justify-center">
          {heroImage && (
            <Image
              src={heroImage.imageUrl}
              alt={heroImage.description}
              fill
              className="object-cover"
              data-ai-hint={heroImage.imageHint}
              priority
            />
          )}
          <div className="absolute inset-0 bg-black/50" />
          <div className="relative z-10 container mx-auto px-4 md:px-6 text-center text-white">
            <h1 className="text-4xl md:text-6xl font-headline font-bold tracking-tight">
              HealthSync AI
            </h1>
            <p className="mt-4 max-w-2xl mx-auto text-lg md:text-xl text-neutral-200">
              Empowering Patients and Researchers with Secure, AI-Driven Data Exchange
            </p>
            <div className="mt-8 flex justify-center">
              <Button asChild size="lg" className="font-headline">
                <Link href="/dashboard">
                  Get Started <ArrowRight className="ml-2" />
                </Link>
              </Button>
            </div>
          </div>
        </section>

        <section className="py-12 md:py-20 bg-background">
          <div className="container mx-auto px-4 md:px-6">
            <h2 className="text-3xl font-bold text-center font-headline mb-2">
              Explore Our Platforms
            </h2>
            <p className="text-center text-muted-foreground max-w-3xl mx-auto mb-12">
              Dedicated interfaces for patients, researchers, and administrators to manage and monitor data with full transparency.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="flex flex-col items-center text-center p-6 rounded-lg border bg-card shadow-sm transition-transform hover:scale-105">
                <h3 className="text-2xl font-semibold font-headline mb-4">Patient Dashboard</h3>
                <p className="text-muted-foreground mb-6 flex-grow">
                  Manage your data sharing preferences with granular control and AI-powered suggestions.
                </p>
                <Button asChild variant="outline">
                  <Link href="/dashboard">Patient Portal <ArrowRight className="ml-2" /></Link>
                </Button>
              </div>
              <div className="flex flex-col items-center text-center p-6 rounded-lg border bg-card shadow-sm transition-transform hover:scale-105">
                <h3 className="text-2xl font-semibold font-headline mb-4">Researcher Portal</h3>
                <p className="text-muted-foreground mb-6 flex-grow">
                  Submit structured queries to discover anonymized datasets for your research.
                </p>
                <Button asChild variant="outline">
                  <Link href="/researcher">Researcher Portal <ArrowRight className="ml-2" /></Link>
                </Button>
              </div>
              <div className="flex flex-col items-center text-center p-6 rounded-lg border bg-card shadow-sm transition-transform hover:scale-105">
                <h3 className="text-2xl font-semibold font-headline mb-4">Agent Monitor</h3>
                <p className="text-muted-foreground mb-6 flex-grow">
                  Observe real-time agent communications and system activities for full transparency.
                </p>
                <Button asChild variant="outline">
                  <Link href="/monitor">Activity Monitor <ArrowRight className="ml-2" /></Link>
                </Button>
              </div>
            </div>
          </div>
        </section>
      </main>
      <footer className="py-6 bg-secondary text-secondary-foreground">
        <div className="container mx-auto px-4 md:px-6 text-center">
          <p className="text-sm">&copy; {new Date().getFullYear()} HealthSync AI. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
