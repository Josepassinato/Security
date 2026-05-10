import type { Metadata } from 'next';
import { FimDashboard } from '@/components/fim/FimDashboard';

export const metadata: Metadata = {
  title: 'File Integrity Monitoring | AiSOC Dashboard',
  description:
    'Real-time osquery file_events telemetry — track file creation, deletion, and modification across your fleet.',
};

/**
 * /dashboard/file-integrity
 *
 * Dedicated dashboard page for File Integrity Monitoring.
 * Reuses the existing FimDashboard component so all FIM functionality
 * (summary cards, event table, time-range picker) is available here as
 * well as at the canonical /fim route.
 */
export default function DashboardFileIntegrityPage() {
  return <FimDashboard />;
}
