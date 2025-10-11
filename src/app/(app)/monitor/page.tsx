import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import type { ActivityLog } from "@/lib/types";
import {
  Bot,
  User,
  Database,
  FlaskConical,
  BrainCircuit,
  ShieldCheck,
  ArrowRight,
} from "lucide-react";

const activityLogs: ActivityLog[] = [
  { id: "1", timestamp: "2024-05-21 10:00:15", agent: "Patient App", action: "Consent Updated", status: "Success" },
  { id: "2", timestamp: "2024-05-21 10:01:02", agent: "AI Consent Agent", action: "Optimize Preferences", status: "Success" },
  { id: "3", timestamp: "2024-05-21 10:05:30", agent: "Researcher Portal", action: "Query Submitted", status: "Success" },
  { id: "4", timestamp: "2024-05-21 10:05:45", agent: "Reasoning Engine", action: "Validate Query", status: "Pending" },
  { id: "5", timestamp: "2024-05-21 10:06:11", agent: "Data Custodian", action: "Fetch Anonymized Data", status: "Success" },
  { id: "6", timestamp: "2024-05-21 10:07:22", agent: "AI Privacy Agent", action: "Aggregate Dataset", status: "Success" },
  { id: "7", timestamp: "2024-05-21 10:08:00", agent: "Researcher Portal", action: "Summary Delivered", status: "Success" },
  { id: "8", timestamp: "2024-05-21 10:15:00", agent: "Data Custodian", action: "Consent Check Failed", status: "Failed" },
];

const agents = [
  { name: "Patient App", icon: User },
  { name: "AI Consent Agent", icon: Bot },
  { name: "Data Custodian", icon: ShieldCheck },
  { name: "AI Privacy Agent", icon: Bot },
  { name: "Reasoning Engine", icon: BrainCircuit },
  { name: "Researcher Portal", icon: FlaskConical },
  { name: "EHR / Datasets", icon: Database },
];

const AgentNode = ({ name, icon: Icon }: { name: string; icon: React.ElementType }) => (
  <div className="flex flex-col items-center gap-2 text-center w-24">
    <div className="flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 text-primary border-2 border-primary/20">
      <Icon className="w-8 h-8" />
    </div>
    <span className="text-xs font-semibold">{name}</span>
  </div>
);

const Arrow = () => (
    <div className="flex-1 flex items-center justify-center -mx-4">
        <ArrowRight className="w-6 h-6 text-muted-foreground/50 hidden md:block"/>
    </div>
)

export default function MonitorPage() {
  return (
    <div className="container mx-auto space-y-8">
      <Card>
        <CardHeader>
          <CardTitle className="font-headline text-2xl">Agent Communication Flow</CardTitle>
          <CardDescription>
            Visualization of agent communication and status.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-6 md:p-8 lg:p-10 overflow-x-auto">
          <div className="flex flex-row md:flex-row items-center justify-between gap-4 md:gap-0 min-w-[700px] md:min-w-full">
             <AgentNode name={agents[0].name} icon={agents[0].icon} />
             <Arrow />
             <AgentNode name={agents[1].name} icon={agents[1].icon} />
             <Arrow />
             <AgentNode name={agents[2].name} icon={agents[2].icon} />
             <Arrow />
             <div className="flex flex-col gap-8">
                <AgentNode name={agents[3].name} icon={agents[3].icon} />
                <AgentNode name={agents[4].name} icon={agents[4].icon} />
             </div>
             <Arrow />
             <AgentNode name={agents[5].name} icon={agents[5].icon} />
             <Arrow />
             <AgentNode name={agents[6].name} icon={agents[6].icon} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="font-headline text-2xl">Real-time Agent Activity</CardTitle>
          <CardDescription>
            Logs and outcomes of agent actions across the system.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp</TableHead>
                <TableHead>Agent</TableHead>
                <TableHead>Action</TableHead>
                <TableHead className="text-right">Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {activityLogs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="font-mono text-xs">{log.timestamp}</TableCell>
                  <TableCell className="font-medium">{log.agent}</TableCell>
                  <TableCell>{log.action}</TableCell>
                  <TableCell className="text-right">
                    <Badge
                      variant={
                        log.status === "Success"
                          ? "default"
                          : log.status === "Pending"
                          ? "secondary"
                          : "destructive"
                      }
                      className={`bg-opacity-20 border-opacity-40 text-foreground
                        ${log.status === 'Success' && 'bg-green-500 border-green-600'}
                        ${log.status === 'Pending' && 'bg-yellow-500 border-yellow-600'}
                        ${log.status === 'Failed' && 'bg-red-500 border-red-600'}
                      `}
                    >
                      {log.status}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
