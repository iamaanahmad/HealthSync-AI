"use client";

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { 
  Download, 
  Share, 
  Copy, 
  FileJson, 
  FileText, 
  FileCode,
  Link,
  Mail,
  CheckCircle,
  AlertCircle,
  Clock
} from "lucide-react";
import { MeTTaResponse, mettaAPI } from "@/lib/metta-api";
import { useToast } from "@/hooks/use-toast";

interface QueryResultsExportProps {
  queryResponse: MeTTaResponse | null;
}

type ExportFormat = 'json' | 'csv' | 'xml';

interface ShareableLink {
  id: string;
  url: string;
  expiresAt: Date;
  accessCount: number;
  maxAccess?: number;
}

export function QueryResultsExport({ queryResponse }: QueryResultsExportProps) {
  const [exportFormat, setExportFormat] = useState<ExportFormat>('json');
  const [isExporting, setIsExporting] = useState(false);
  const [shareableLinks, setShareableLinks] = useState<ShareableLink[]>([]);
  const [emailRecipient, setEmailRecipient] = useState('');
  const [shareMessage, setShareMessage] = useState('');
  const [maxAccess, setMaxAccess] = useState<number | undefined>(undefined);
  const { toast } = useToast();

  const getFormatIcon = (format: ExportFormat) => {
    switch (format) {
      case 'json':
        return <FileJson className="h-4 w-4" />;
      case 'csv':
        return <FileText className="h-4 w-4" />;
      case 'xml':
        return <FileCode className="h-4 w-4" />;
    }
  };

  const getFormatDescription = (format: ExportFormat) => {
    switch (format) {
      case 'json':
        return 'JavaScript Object Notation - structured data format';
      case 'csv':
        return 'Comma Separated Values - spreadsheet compatible';
      case 'xml':
        return 'Extensible Markup Language - structured document format';
    }
  };

  const exportResults = async () => {
    if (!queryResponse) {
      toast({
        title: "Error",
        description: "No query results to export",
        variant: "destructive",
      });
      return;
    }

    setIsExporting(true);
    
    try {
      const blob = await mettaAPI.exportResults(queryResponse.query_id, exportFormat);
      
      // Create download link
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `metta-query-${queryResponse.query_id}.${exportFormat}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      toast({
        title: "Export Successful",
        description: `Results exported as ${exportFormat.toUpperCase()}`,
      });
    } catch (error) {
      console.error('Export failed:', error);
      toast({
        title: "Export Failed",
        description: "Failed to export query results",
        variant: "destructive",
      });
    } finally {
      setIsExporting(false);
    }
  };

  const copyToClipboard = async () => {
    if (!queryResponse) return;

    try {
      let content: string;
      
      switch (exportFormat) {
        case 'json':
          content = JSON.stringify({
            query_id: queryResponse.query_id,
            results: queryResponse.results,
            reasoning_path: queryResponse.reasoning_path,
            confidence_score: queryResponse.confidence_score,
            timestamp: queryResponse.timestamp
          }, null, 2);
          break;
        case 'csv':
          if (queryResponse.results.length > 0) {
            const headers = Object.keys(queryResponse.results[0]);
            const csvRows = [
              headers.join(','),
              ...queryResponse.results.map(row => 
                headers.map(header => JSON.stringify(row[header] || '')).join(',')
              )
            ];
            content = csvRows.join('\n');
          } else {
            content = 'No results to export';
          }
          break;
        case 'xml':
          content = `<?xml version="1.0" encoding="UTF-8"?>
<query_results>
  <query_id>${queryResponse.query_id}</query_id>
  <confidence_score>${queryResponse.confidence_score}</confidence_score>
  <timestamp>${queryResponse.timestamp}</timestamp>
  <results>
${queryResponse.results.map(result => 
  `    <result>${Object.entries(result).map(([key, value]) => 
    `<${key}>${value}</${key}>`
  ).join('')}</result>`
).join('\n')}
  </results>
</query_results>`;
          break;
      }

      await navigator.clipboard.writeText(content);
      toast({
        title: "Copied to Clipboard",
        description: `Results copied as ${exportFormat.toUpperCase()}`,
      });
    } catch (error) {
      console.error('Copy failed:', error);
      toast({
        title: "Copy Failed",
        description: "Failed to copy results to clipboard",
        variant: "destructive",
      });
    }
  };

  const generateShareableLink = () => {
    if (!queryResponse) return;

    // Generate mock shareable link
    const linkId = `share_${Date.now()}`;
    const shareableLink: ShareableLink = {
      id: linkId,
      url: `${window.location.origin}/shared/query/${linkId}`,
      expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000), // 7 days
      accessCount: 0,
      maxAccess: maxAccess
    };

    setShareableLinks(prev => [shareableLink, ...prev]);
    
    toast({
      title: "Shareable Link Created",
      description: "Link copied to clipboard",
    });

    // Copy to clipboard
    navigator.clipboard.writeText(shareableLink.url);
  };

  const sendByEmail = () => {
    if (!queryResponse || !emailRecipient) {
      toast({
        title: "Error",
        description: "Please enter a valid email address",
        variant: "destructive",
      });
      return;
    }

    // Generate email content
    const subject = `MeTTa Query Results - ${queryResponse.query_id}`;
    const body = `
${shareMessage || 'Please find the MeTTa query results below:'}

Query ID: ${queryResponse.query_id}
Confidence Score: ${(queryResponse.confidence_score * 100).toFixed(1)}%
Results Count: ${queryResponse.results.length}
Timestamp: ${new Date(queryResponse.timestamp).toLocaleString()}

Results:
${JSON.stringify(queryResponse.results, null, 2)}

Reasoning Path:
${queryResponse.reasoning_path.map((step, index) => `${index + 1}. ${step}`).join('\n')}
    `.trim();

    // Open email client
    const mailtoUrl = `mailto:${emailRecipient}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    window.open(mailtoUrl);

    toast({
      title: "Email Client Opened",
      description: "Email draft created with query results",
    });
  };

  const revokeShareableLink = (linkId: string) => {
    setShareableLinks(prev => prev.filter(link => link.id !== linkId));
    toast({
      title: "Link Revoked",
      description: "Shareable link has been revoked",
    });
  };

  if (!queryResponse) {
    return (
      <Card>
        <CardContent className="text-center py-12">
          <Download className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">No Results to Export</h3>
          <p className="text-muted-foreground">
            Execute a query to export and share results
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Export Options */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Download className="h-5 w-5" />
            Export Results
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Export Format</Label>
              <Select value={exportFormat} onValueChange={(value: ExportFormat) => setExportFormat(value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="json">
                    <div className="flex items-center gap-2">
                      <FileJson className="h-4 w-4" />
                      JSON
                    </div>
                  </SelectItem>
                  <SelectItem value="csv">
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4" />
                      CSV
                    </div>
                  </SelectItem>
                  <SelectItem value="xml">
                    <div className="flex items-center gap-2">
                      <FileCode className="h-4 w-4" />
                      XML
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                {getFormatDescription(exportFormat)}
              </p>
            </div>

            <div className="space-y-2">
              <Label>Quick Actions</Label>
              <div className="flex gap-2">
                <Button 
                  onClick={exportResults}
                  disabled={isExporting}
                  className="flex-1"
                >
                  {getFormatIcon(exportFormat)}
                  {isExporting ? 'Exporting...' : 'Download'}
                </Button>
                <Button 
                  variant="outline" 
                  onClick={copyToClipboard}
                  className="flex-1"
                >
                  <Copy className="h-4 w-4" />
                  Copy
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Query Info</Label>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Results:</span>
                  <span>{queryResponse.results.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Confidence:</span>
                  <Badge variant={queryResponse.confidence_score >= 0.8 ? "default" : "secondary"}>
                    {(queryResponse.confidence_score * 100).toFixed(1)}%
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Query ID:</span>
                  <span className="font-mono text-xs">{queryResponse.query_id}</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Sharing Options */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Share className="h-5 w-5" />
            Share Results
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Generate Shareable Link */}
            <div className="space-y-3">
              <Label>Generate Shareable Link</Label>
              <div className="space-y-2">
                <div className="flex gap-2">
                  <Input
                    type="number"
                    placeholder="Max access count (optional)"
                    value={maxAccess || ''}
                    onChange={(e) => setMaxAccess(e.target.value ? parseInt(e.target.value) : undefined)}
                    className="flex-1"
                  />
                  <Button onClick={generateShareableLink}>
                    <Link className="h-4 w-4 mr-2" />
                    Generate
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  Create a secure link that expires in 7 days
                </p>
              </div>
            </div>

            {/* Send by Email */}
            <div className="space-y-3">
              <Label>Send by Email</Label>
              <div className="space-y-2">
                <Input
                  type="email"
                  placeholder="recipient@example.com"
                  value={emailRecipient}
                  onChange={(e) => setEmailRecipient(e.target.value)}
                />
                <Textarea
                  placeholder="Optional message..."
                  value={shareMessage}
                  onChange={(e) => setShareMessage(e.target.value)}
                  className="min-h-16"
                />
                <Button onClick={sendByEmail} className="w-full">
                  <Mail className="h-4 w-4 mr-2" />
                  Send Email
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Active Shareable Links */}
      {shareableLinks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Link className="h-5 w-5" />
              Active Shareable Links
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-64">
              <div className="space-y-3">
                {shareableLinks.map((link) => (
                  <div
                    key={link.id}
                    className="p-4 rounded-lg border bg-muted/30"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Link className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium text-sm">Shareable Link</span>
                        <Badge variant="outline" className="text-xs">
                          {link.accessCount} / {link.maxAccess || '∞'} views
                        </Badge>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => revokeShareableLink(link.id)}
                      >
                        Revoke
                      </Button>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Input
                          value={link.url}
                          readOnly
                          className="font-mono text-xs"
                        />
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => navigator.clipboard.writeText(link.url)}
                        >
                          <Copy className="h-3 w-3" />
                        </Button>
                      </div>
                      
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          Expires: {link.expiresAt.toLocaleDateString()}
                        </div>
                        <div className="flex items-center gap-1">
                          {link.accessCount === 0 ? (
                            <AlertCircle className="h-3 w-3 text-yellow-500" />
                          ) : (
                            <CheckCircle className="h-3 w-3 text-green-500" />
                          )}
                          {link.accessCount === 0 ? 'Not accessed' : `${link.accessCount} views`}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}

      {/* Results Preview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {getFormatIcon(exportFormat)}
            Results Preview ({exportFormat.toUpperCase()})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-64">
            <pre className="text-sm font-mono whitespace-pre-wrap">
              {exportFormat === 'json' && JSON.stringify({
                query_id: queryResponse.query_id,
                results: queryResponse.results,
                reasoning_path: queryResponse.reasoning_path,
                confidence_score: queryResponse.confidence_score,
                timestamp: queryResponse.timestamp
              }, null, 2)}
              
              {exportFormat === 'csv' && queryResponse.results.length > 0 && (() => {
                const headers = Object.keys(queryResponse.results[0]);
                const csvRows = [
                  headers.join(','),
                  ...queryResponse.results.map(row => 
                    headers.map(header => JSON.stringify(row[header] || '')).join(',')
                  )
                ];
                return csvRows.join('\n');
              })()}
              
              {exportFormat === 'xml' && `<?xml version="1.0" encoding="UTF-8"?>
<query_results>
  <query_id>${queryResponse.query_id}</query_id>
  <confidence_score>${queryResponse.confidence_score}</confidence_score>
  <timestamp>${queryResponse.timestamp}</timestamp>
  <results>
${queryResponse.results.map(result => 
  `    <result>${Object.entries(result).map(([key, value]) => 
    `<${key}>${value}</${key}>`
  ).join('')}</result>`
).join('\n')}
  </results>
</query_results>`}
            </pre>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}