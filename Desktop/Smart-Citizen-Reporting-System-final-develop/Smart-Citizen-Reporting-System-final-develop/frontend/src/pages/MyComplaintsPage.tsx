import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AppLayout } from "@/components/AppLayout";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Search, Plus, MapPin, Calendar } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { fetchReports } from "@/services/reports";
import { useLookups } from "@/hooks/useLookups";
import { deriveTitle, formatDate, formatCoords, getPriorityLabel, getPriorityStyle, getStatusStyle, getCategoryMacedonianName } from "@/lib/reportHelpers";

export default function MyComplaintsPage() {
  const navigate = useNavigate();
  const { categories, statuses, categoryLabel, statusLabel } = useLookups();

  const { data: reports = [], isLoading, error, refetch } = useQuery({
    queryKey: ["reports"],
    queryFn: fetchReports,
  });

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [categoryFilter, setCategoryFilter] = useState("all");

  const filtered = reports.filter((r) => {
    const matchSearch = r.description.toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === "all" || String(r.status_id) === statusFilter;
    const matchCategory = categoryFilter === "all" || String(r.category_id) === categoryFilter;
    return matchSearch && matchStatus && matchCategory;
  });

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Мои пријави</h1>
            <p className="text-muted-foreground text-sm">Прегледајте го статусот и историјата на вашите поднесени проблеми.</p>
          </div>
          <Button onClick={() => navigate("/new-complaint")}>
            <Plus className="mr-2 h-4 w-4" /> Нова пријава
          </Button>
        </div>

        {/* Filters */}
        <Card>
          <CardContent className="py-3 flex flex-wrap gap-3 items-center">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Пребарај по опис..." className="pl-9" value={search} onChange={(e) => setSearch(e.target.value)} />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40"><SelectValue placeholder="Статус" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Сите статуси</SelectItem>
                {statuses.map((s) => (
                  <SelectItem key={s.id} value={String(s.id)}>{s.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-44"><SelectValue placeholder="Категорија" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Сите категории</SelectItem>
                {categories.map((c) => (
                  <SelectItem key={c.id} value={String(c.id)}>{getCategoryMacedonianName(c.name)}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </CardContent>
        </Card>

        {/* Loading */}
        {isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <Card key={i}><CardContent className="p-5 space-y-3"><Skeleton className="h-5 w-3/4" /><Skeleton className="h-4 w-full" /><Skeleton className="h-3 w-1/2" /></CardContent></Card>
            ))}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="text-center py-12 text-destructive">
            <p className="font-semibold">Грешка</p>
            <p className="text-sm">{(error as Error).message ?? "Грешка при вчитување."}</p>
            <Button variant="outline" className="mt-4" onClick={() => refetch()}>Обиди се повторно</Button>
          </div>
        )}

        {/* Cards */}
        {!isLoading && !error && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filtered.map((r) => (
                <Card key={r.id} className="hover:shadow-md transition-shadow cursor-pointer group" onClick={() => navigate(`/complaints/${r.id}`)}>
                  <CardContent className="p-5 space-y-3">
                    <div className="flex justify-between items-start">
                      <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors line-clamp-2">{deriveTitle(r.description)}</h3>
                      <Badge variant="outline" className={getStatusStyle(r.status_id)}>{statusLabel(r.status_id)}</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground line-clamp-2">{r.description}</p>
                    {r.latitude != null && r.longitude != null && (
                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <MapPin className="h-3 w-3" />{formatCoords(r.latitude, r.longitude)}
                      </div>
                    )}
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-1 text-xs text-muted-foreground"><Calendar className="h-3 w-3" />{formatDate(r.created_at)}</span>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className={`text-xs ${getPriorityStyle(r.priority)}`}>
                          {getPriorityLabel(r.priority)}
                        </Badge>
                        <Badge variant="secondary" className="text-xs">{categoryLabel(r.category_id)}</Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
            {filtered.length === 0 && (
              <div className="text-center py-12 text-muted-foreground">Не се пронајдени пријави со вашите филтри.</div>
            )}
            <p className="text-sm text-muted-foreground">Прикажани {filtered.length} од {reports.length} пријави</p>
          </>
        )}
      </div>
    </AppLayout>
  );
}
