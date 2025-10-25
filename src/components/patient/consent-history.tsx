"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { 
  History, 
  RefreshCw, 
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Filter
} from 'lucide-react';
import { 
  PatientConsentApi, 
  DataTypes,
  type ConsentRecord 
} from '@/lib/patient-consent-api';
import { AuthService } from '@/lib/auth';
import { useToast } from '@/hooks/use-toast';
import { format } from 'date-fns';

interface ConsentHistoryProps {
  refreshTrigger?: number;
}

export function ConsentHistory({ refreshTrigger }: ConsentHistoryProps) {
  const [history, setHistory] = useState<ConsentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterDataType, setFilterDataType] = useState<string>('all');
  const { toast } = useToast();

  const loadHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const session = AuthService.getCurrentSession();
      if (!session?.patientId) {
        throw new Error('No patient session found');
      }

      const dataTypeFilter = filterDataType === 'all' ? undefined : filterDataType;
      const result = await PatientConsentApi.getConsentHistory(session.patientId, dataTypeFilter);
      
      if (result.success && result.data) {
        setHistory(result.data);
      } else {
        throw new Error(result.error || 'Failed to load consent history');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load consent history';
      setError(errorMessage);
      toast({
        title: 'Error Loading History',
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, [filterDataType, refreshTrigger]);

  const formatDateTime = (dateString: string) => {
    try {
      return format(new Date(dateString), 'MMM d, yyyy \'at\' h:mm a');
    } catch {
      return dateString;
    }
  };

  const getStatusBadge = (consent: ConsentRecord) => {
    if (consent.consentGranted) {
      const isExpiring = PatientConsentApi.isConsentExpiringSoon(consent);
      return (
        <Badge variant={isExpiring ? "destructive" : "default"} className="text-xs">
          <CheckCircle className="w-3 h-3 mr-1" />
          {isExpiring ? 'Expiring Soon' : 'Active'}
        </Badge>
      );
    } else {
      return (
        <Badge variant="secondary" className="text-xs">
          <XCircle className="w-3 h-3 mr-1" />
          Revoked
        </Badge>
      );
    }
  };

  const getVersionBadge = (version: number) => {
    return (
      <Badge variant="outline" className="text-xs">
        v{version}
      </Badge>
    );
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center space-x-2">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span>Loading consent history...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              {error}
              <Button 
                variant="outline" 
                size="sm" 
                className="ml-4" 
                onClick={loadHistory}
              >
                Retry
              </Button>
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <History className="h-5 w-5" />
              Consent History
            </CardTitle>
            <CardDescription>
              Track all changes to your data sharing preferences over time
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4" />
            <Select value={filterDataType} onValueChange={setFilterDataType}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by data type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Data Types</SelectItem>
                {Object.entries(DataTypes).map(([key, dataType]) => (
                  <SelectItem key={dataType} value={dataType}>
                    {PatientConsentApi.getDataTypeLabel(dataType)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm" onClick={loadHistory}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {history.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <History className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No consent history found</p>
            {filterDataType !== 'all' && (
              <p className="text-sm mt-2">
                Try changing the filter or{' '}
                <Button 
                  variant="link" 
                  className="p-0 h-auto" 
                  onClick={() => setFilterDataType('all')}
                >
                  view all data types
                </Button>
              </p>
            )}
          </div>
        ) : (
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Data Type</TableHead>
                  <TableHead>Research Category</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Version</TableHead>
                  <TableHead>Last Updated</TableHead>
                  <TableHead>Expires</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {history.map((consent) => (
                  <TableRow key={consent.consentId}>
                    <TableCell className="font-medium">
                      {PatientConsentApi.getDataTypeLabel(consent.dataType)}
                    </TableCell>
                    <TableCell>
                      {PatientConsentApi.getResearchCategoryLabel(consent.researchCategory)}
                    </TableCell>
                    <TableCell>
                      {getStatusBadge(consent)}
                    </TableCell>
                    <TableCell>
                      {getVersionBadge(consent.version)}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Clock className="h-3 w-3 text-muted-foreground" />
                        <span className="text-sm">
                          {formatDateTime(consent.lastUpdated)}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm">
                        {format(new Date(consent.expiryDate), 'MMM d, yyyy')}
                      </span>
                      {PatientConsentApi.isConsentExpiringSoon(consent) && (
                        <Badge variant="destructive" className="ml-2 text-xs">
                          Soon
                        </Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}