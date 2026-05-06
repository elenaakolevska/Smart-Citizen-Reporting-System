import { useLookups } from "@/hooks/useLookups";
import { formatDate } from "@/lib/reportHelpers";
import { Badge } from "@/components/ui/badge";
import { getStatusStyle } from "@/lib/reportHelpers";

export interface HistoryEntry {
  id: string | number;
  status_id: number;
  created_at: string;
}

interface Props {
  entries: HistoryEntry[];
}

export function StatusTimeline({ entries }: Props) {
  const { statusLabel } = useLookups();
  const sorted = [...entries].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  if (sorted.length === 0) {
    return <p className="text-sm text-muted-foreground italic">Нема историја на статус.</p>;
  }

  return (
    <div className="relative space-y-0">
      {sorted.map((entry, i) => (
        <div key={entry.id} className="flex gap-4 pb-6 last:pb-0">
          {/* vertical line + dot */}
          <div className="flex flex-col items-center">
            <div className="h-3 w-3 rounded-full bg-primary shrink-0 mt-1" />
            {i < sorted.length - 1 && <div className="w-px flex-1 bg-border" />}
          </div>
          {/* content */}
          <div className="space-y-1">
            <Badge variant="outline" className={getStatusStyle(entry.status_id)}>
              {statusLabel(entry.status_id)}
            </Badge>
            <p className="text-xs text-muted-foreground">{formatDate(entry.created_at)}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
