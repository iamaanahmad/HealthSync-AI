"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { CircleUser, LogOut, Settings, HelpCircle } from "lucide-react";
import { AuthService, type PatientProfile } from '@/lib/auth';
import { useToast } from '@/hooks/use-toast';

export function Header() {
  const [profile, setProfile] = useState<PatientProfile | null>(null);
  const router = useRouter();
  const { toast } = useToast();

  useEffect(() => {
    const session = AuthService.getCurrentSession();
    if (session?.profile) {
      setProfile(session.profile);
    }
  }, []);

  const handleLogout = () => {
    AuthService.logout();
    toast({
      title: 'Logged Out',
      description: 'You have been successfully logged out.',
    });
    router.push('/');
  };

  const getInitials = (firstName: string, lastName: string) => {
    return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();
  };

  return (
    <header className="flex h-14 items-center gap-4 border-b bg-card px-4 lg:h-[60px] lg:px-6">
      <SidebarTrigger className="md:hidden" />
      <div className="w-full flex-1">
        {profile && (
          <div className="hidden md:flex items-center text-sm text-muted-foreground">
            Welcome back, {profile.firstName}!
          </div>
        )}
      </div>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="secondary" size="icon" className="rounded-full">
            {profile ? (
              <Avatar className="h-8 w-8">
                <AvatarFallback className="text-xs">
                  {getInitials(profile.firstName, profile.lastName)}
                </AvatarFallback>
              </Avatar>
            ) : (
              <CircleUser className="h-5 w-5" />
            )}
            <span className="sr-only">Toggle user menu</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuLabel>
            {profile ? `${profile.firstName} ${profile.lastName}` : 'My Account'}
          </DropdownMenuLabel>
          {profile && (
            <DropdownMenuLabel className="text-xs text-muted-foreground font-normal">
              ID: {profile.patientId}
            </DropdownMenuLabel>
          )}
          <DropdownMenuSeparator />
          <DropdownMenuItem>
            <Settings className="mr-2 h-4 w-4" />
            Settings
          </DropdownMenuItem>
          <DropdownMenuItem>
            <HelpCircle className="mr-2 h-4 w-4" />
            Support
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={handleLogout} className="text-destructive">
            <LogOut className="mr-2 h-4 w-4" />
            Logout
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  );
}
