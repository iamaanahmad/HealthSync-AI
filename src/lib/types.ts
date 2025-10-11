export type ActivityLog = {
  id: string;
  timestamp: string;
  agent: string;
  action: string;
  status: 'Success' | 'Pending' | 'Failed';
};
