import { AppLayout } from "@/components/AppLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Search, MoreHorizontal, ExternalLink } from "lucide-react";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchReports } from "@/services/reports";
import { useLookups } from "@/hooks/useLookups";
import { useNavigate } from "react-router-dom";
import {
  deriveTitle,
  formatDate,
  getStatusStyle,
  getPriorityStyle,
  formatPriority,
} from "@/lib/reportHelpers";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export default function ManageComplaintsPage() {
  const [search, setSearch] = useState("");
  const navigate = useNavigate();
  const { categoryLabel, statusLabel } = useLookups();

  const { data: reports, isLoading, error } = useQuery({
    queryKey: ["reports", "all"],
    queryFn: fetchReports,
  });

  const filtered = reports?.filter((r) =>
    r.description.toLowerCase().includes(search.toLowerCase())
  ) || [];

  if (isLoading) {
    return (
      <AppLayout>
        <div className="space-y-6">
          <Skeleton className="h-10 w-48" />
          <Card>
            <CardHeader><Skeleton className="h-8 w-full" /></CardHeader>
            <CardContent><Skeleton className="h-64 w-full" /></CardContent>
          </Card>
        </div>
      </AppLayout>
    );
  }

  if (error) {
    return (
      <AppLayout>
        <div className="text-center py-12 text-destructive">Грешка при вчитување на пријавите.</div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Управување со пријави</h1>
          <p className="text-muted-foreground text-sm">Прегледајте и управувајте со сите пријави во системот.</p>
        </div>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <CardTitle>Сите пријави</CardTitle>
              <div className="relative w-full sm:w-64">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Пребарај по опис..."
                  className="pl-9"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-muted-foreground">
                    <th className="text-left py-3 px-2 font-medium">ID</th>
                    <th className="text-left py-3 px-2 font-medium">Опис</th>
                    <th className="text-left py-3 px-2 font-medium">Категорија</th>
                    <th className="text-left py-3 px-2 font-medium">Статус</th>
                    <th className="text-left py-3 px-2 font-medium">Приоритет</th>
                    <th className="text-left py-3 px-2 font-medium">Датум</th>
                    <th className="text-left py-3 px-2 font-medium">Акции</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center py-8 text-muted-foreground">
                        Нема пронајдено пријави.
                      </td>
                    </tr>
                  ) : (
                    filtered.map((r) => (
                      <tr key={r.id} className="border-b last:border-0 hover:bg-secondary/50 transition-colors group">
                        <td className="py-3 px-2 font-mono text-muted-foreground text-xs">{r.id}</td>
                        <td className="py-3 px-2 font-medium text-foreground max-w-[200px] truncate">
                          {deriveTitle(r.description)}
                        </td>
                        <td className="py-3 px-2 text-muted-foreground">
                          <Badge variant="outline" className="font-normal">{categoryLabel(r.category_id)}</Badge>
                        </td>
                        <td className="py-3 px-2">
                          <Badge variant="outline" className={getStatusStyle(r.status_id)}>
                            {statusLabel(r.status_id)}
                          </Badge>
                        </td>
                        <td className="py-3 px-2">
                          <Badge variant="outline" className={`${getPriorityStyle(r.priority)}`}>
                            {formatPriority(r.priority)}
                          </Badge>
                        </td>
                        <td className="py-3 px-2 text-muted-foreground">{formatDate(r.created_at)}</td>
                        <td className="py-3 px-2">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => navigate(`/complaints/${r.id}`)}>
                                <ExternalLink className="mr-2 h-4 w-4" /> Детали
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
