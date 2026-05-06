import { AppLayout } from "@/components/AppLayout";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search, Eye } from "lucide-react";
import { useState } from "react";
import { fetchReports, updateReportPriority, type PriorityValue } from "@/services/reports";
import { useLookups } from "@/hooks/useLookups";
import { deriveTitle, formatDate, getPriorityLabel, getPriorityStyle, getStatusStyle, getCategoryMacedonianName } from "@/lib/reportHelpers";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";

const PRIORITY_OPTIONS: PriorityValue[] = ["Низок", "Среден", "Висок", "Итен"];

export default function ManageComplaintsPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { categoryLabel, statusLabel } = useLookups();
  const [search, setSearch] = useState("");

  const { data: reports = [], isLoading } = useQuery({
    queryKey: ["reports"],
    queryFn: fetchReports,
  });

  const priorityMutation = useMutation({
    mutationFn: ({ reportId, priority }: { reportId: string; priority: PriorityValue }) =>
      updateReportPriority(reportId, priority),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports"] });
      toast({ title: "Успешно", description: "Приоритетот е ажуриран." });
    },
    onError: (err: Error) => {
      toast({
        title: "Грешка",
        description: err.message ?? "Неуспешно ажурирање на приоритет.",
        variant: "destructive",
      });
    },
  });

  const filtered = reports.filter((r) =>
    r.description.toLowerCase().includes(search.toLowerCase()) ||
    String(r.id).includes(search.trim()) ||
    (r.priority ?? "").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Управување со пријави</h1>
          <p className="text-muted-foreground text-sm">Прегледајте и управувајте со сите пријави во системот.</p>
        </div>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle>Сите пријави</CardTitle>
              <div className="relative w-64">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input placeholder="Пребарај пријави..." className="pl-9" value={search} onChange={(e) => setSearch(e.target.value)} />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-muted-foreground">
                    {/* <th className="text-left py-3 px-2 font-medium">ID</th> */}
                    <th className="text-left py-3 px-2 font-medium">Наслов</th>
                    <th className="text-left py-3 px-2 font-medium">Граѓанин</th>
                    <th className="text-left py-3 px-2 font-medium">Категорија</th>
                    <th className="text-left py-3 px-2 font-medium">Статус</th>
                    <th className="text-left py-3 px-2 font-medium">Приоритет</th>
                    <th className="text-left py-3 px-2 font-medium">Датум</th>
                    <th className="text-left py-3 px-2 font-medium">Акции</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((r) => {
                    // Extract username from email
                    let username = r.user_email ? r.user_email.split("@")[0] : r.user_id?.slice(0, 8);
                    // Translate category name using shared helper
                    let categoryName = categoryLabel(r.category_id);
                    let mkCategory = getCategoryMacedonianName(categoryName);
                    return (
                      <tr key={r.id} className="border-b last:border-0 hover:bg-secondary/50 transition-colors">
                        <td className="py-3 px-2 font-medium text-foreground">{deriveTitle(r.description)}</td>
                        <td className="py-3 px-2 text-muted-foreground">{username}</td>
                        <td className="py-3 px-2 text-muted-foreground">{mkCategory}</td>
                        <td className="py-3 px-2">
                          <Badge variant="outline" className={getStatusStyle(r.status_id)}>
                            {statusLabel(r.status_id)}
                          </Badge>
                        </td>
                        <td className="py-3 px-2">
                          <Badge variant="outline" className={getPriorityStyle(r.priority)}>
                            {getPriorityLabel(r.priority)}
                          </Badge>
                        </td>
                        <td className="py-3 px-2 text-muted-foreground">{formatDate(r.created_at)}</td>
                        <td className="py-3 px-2">
                          <Button variant="ghost" size="sm" onClick={() => navigate(`/complaints/${r.id}`)}>
                            <Eye className="h-4 w-4" />
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                  {!isLoading && filtered.length === 0 && (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-muted-foreground">
                        Нема пријави за прикажување.
                      </td>
                    </tr>
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
