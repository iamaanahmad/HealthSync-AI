"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import { 
  User, 
  Mail, 
  Phone, 
  Calendar, 
  UserCheck, 
  Edit,
  Shield,
  Clock
} from 'lucide-react';
import { AuthService, type PatientProfile } from '@/lib/auth';
import { format } from 'date-fns';

interface ProfileCardProps {
  onEdit?: () => void;
}

export function ProfileCard({ onEdit }: ProfileCardProps) {
  const [profile, setProfile] = useState<PatientProfile | null>(null);
  const [sessionInfo, setSessionInfo] = useState<{
    sessionToken: string;
    expiresAt: Date;
  } | null>(null);

  useEffect(() => {
    const session = AuthService.getCurrentSession();
    if (session) {
      setProfile(session.profile);
      setSessionInfo({
        sessionToken: session.sessionToken,
        expiresAt: session.expiresAt,
      });
    }
  }, []);

  if (!profile) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-muted-foreground">Profile information not available</p>
        </CardContent>
      </Card>
    );
  }

  const getInitials = (firstName: string, lastName: string) => {
    return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'MMMM d, yyyy');
    } catch {
      return dateString;
    }
  };

  const calculateAge = (dateOfBirth: string) => {
    try {
      const today = new Date();
      const birthDate = new Date(dateOfBirth);
      let age = today.getFullYear() - birthDate.getFullYear();
      const monthDiff = today.getMonth() - birthDate.getMonth();
      
      if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        age--;
      }
      
      return age;
    } catch {
      return null;
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Avatar className="h-16 w-16">
              <AvatarFallback className="text-lg font-semibold">
                {getInitials(profile.firstName, profile.lastName)}
              </AvatarFallback>
            </Avatar>
            <div>
              <CardTitle className="text-2xl font-headline">
                {profile.firstName} {profile.lastName}
              </CardTitle>
              <CardDescription className="flex items-center gap-2">
                <Badge variant="secondary" className="text-xs">
                  ID: {profile.patientId}
                </Badge>
                <Badge variant="outline" className="text-xs">
                  <Shield className="w-3 h-3 mr-1" />
                  Verified Patient
                </Badge>
              </CardDescription>
            </div>
          </div>
          {onEdit && (
            <Button variant="outline" size="sm" onClick={onEdit}>
              <Edit className="w-4 h-4 mr-2" />
              Edit Profile
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Personal Information */}
        <div>
          <h3 className="text-lg font-semibold mb-3 flex items-center">
            <User className="w-5 h-5 mr-2" />
            Personal Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center space-x-3">
              <Calendar className="w-4 h-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Date of Birth</p>
                <p className="text-sm text-muted-foreground">
                  {formatDate(profile.dateOfBirth)}
                  {calculateAge(profile.dateOfBirth) && (
                    <span className="ml-2">({calculateAge(profile.dateOfBirth)} years old)</span>
                  )}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <Mail className="w-4 h-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Email</p>
                <p className="text-sm text-muted-foreground">{profile.email}</p>
              </div>
            </div>
            {profile.phone && (
              <div className="flex items-center space-x-3">
                <Phone className="w-4 h-4 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">Phone</p>
                  <p className="text-sm text-muted-foreground">{profile.phone}</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Emergency Contact */}
        {profile.emergencyContact && (
          <>
            <Separator />
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center">
                <UserCheck className="w-5 h-5 mr-2" />
                Emergency Contact
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium">Name</p>
                  <p className="text-sm text-muted-foreground">{profile.emergencyContact.name}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Relationship</p>
                  <p className="text-sm text-muted-foreground">{profile.emergencyContact.relationship}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Phone</p>
                  <p className="text-sm text-muted-foreground">{profile.emergencyContact.phone}</p>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Session Information */}
        {sessionInfo && (
          <>
            <Separator />
            <div>
              <h3 className="text-lg font-semibold mb-3 flex items-center">
                <Clock className="w-5 h-5 mr-2" />
                Session Information
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium">Session Token</p>
                  <p className="text-sm text-muted-foreground font-mono">
                    {sessionInfo.sessionToken.substring(0, 16)}...
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium">Session Expires</p>
                  <p className="text-sm text-muted-foreground">
                    {format(sessionInfo.expiresAt, 'PPpp')}
                  </p>
                </div>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}