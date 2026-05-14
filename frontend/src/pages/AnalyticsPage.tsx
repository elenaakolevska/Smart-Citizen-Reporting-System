import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { FileText, CheckCircle, Clock, Users, Download, FileSpreadsheet, Loader2 } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, Legend } from "recharts";
import { fetchAnalyticsSummary, exportToCsv, exportToPdf, fetchCategoryRatings } from "@/services/analytics";
import { useToast } from "@/hooks/use-toast";
import { getCategoryMacedonianName } from "@/lib/reportHelpers";
import { useRole } from "@/context/RoleContext";

const COLORS = ["hsl(142, 71%, 45%)", "hsl(38, 92%, 50%)"];

export default function AnalyticsPage() {
  const { toast } = useToast();
  const { role } = useRole();
  const [exportingCsv, setExportingCsv] = useState(false);
  const [exportingPdf, setExportingPdf] = useState(false);
  const [ratingSort, setRatingSort] = useState<"desc" | "asc">("desc");

  const canViewFullAnalytics = role === "admin" || role === "officer";

  const { data, isLoading: isSummaryLoading, error: summaryError } = useQuery({
    queryKey: ["analytics", "summary"],
    queryFn: fetchAnalyticsSummary,
  });

  const { data: ratingData, isLoading: isRatingsLoading } = useQuery({
    queryKey: ["analytics", "ratings"],
    queryFn: fetchCategoryRatings,
    enabled: canViewFullAnalytics,
  });

  const isLoading = isSummaryLoading || (canViewFullAnalytics && isRatingsLoading);
  const error = summaryError;

  const handleExportCsv = async () => {
    setExportingCsv(true);
    try {
      await exportToCsv();
      toast({ title: "Успешно!", description: "CSV извештајот е генериран." });
    } catch (err) {
      toast({ title: "Грешка", description: "Грешка при извоз во CSV.", variant: "destructive" });
    } finally {
      setExportingCsv(false);
    }
  };

  const handleExportPdf = async () => {
    setExportingPdf(true);
    try {
      await exportToPdf();
      toast({ title: "Успешно!", description: "PDF извештајот е генериран." });
    } catch (err) {
      toast({ title: "Грешка", description: "Грешка при извоз во PDF.", variant: "destructive" });
    } finally {
      setExportingPdf(false);
    }
  };

  if (isLoading) {
    return (

        <div className="space-y-6">
          <div className="flex justify-between items-end">
            <div className="space-y-2">
              <Skeleton className="h-8 w-48" />
              <Skeleton className="h-4 w-64" />
            </div>
            <div className="flex gap-2">
              <Skeleton className="h-9 w-24" />
              <Skeleton className="h-9 w-24" />
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Card key={i}><CardContent className="py-5 space-y-2"><Skeleton className="h-10 w-full" /><Skeleton className="h-4 w-1/2" /></CardContent></Card>
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <Skeleton className="lg:col-span-2 h-[350px]" />
            <Skeleton className="h-[350px]" />
          </div>
        </div>

    );
  }

  if (error || !data) {
    return (

        <div className="text-center py-12 text-destructive">
          <p className="font-semibold">Грешка при вчитување на аналитиката.</p>
          <Button variant="outline" className="mt-4" onClick={() => window.location.reload()}>Обиди се повторно</Button>
        </div>

    );
  }

  const statCards = [
    { label: "ВКУПНО ПРИЈАВИ", value: data.kpis.total, icon: FileText, color: "text-primary" },
    { label: "РЕШЕНИ СЛУЧАИ", value: data.kpis.resolved, icon: CheckCircle, color: "text-success" },
    { label: "ПРОСЕЧНО ВРЕМЕ", value: data.kpis.avgTime, icon: Clock, color: "text-warning" },
    { label: "АКТИВНИ ПРИЈАВИ", value: data.kpis.active.toLocaleString(), icon: Users, color: "text-info" },
  ];
  const categoryChartData = data.categoryData.map((category) => ({
    ...category,
    name: getCategoryMacedonianName(category.name),
  }));

  return (
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Аналитички преглед</h1>
            <p className="text-muted-foreground text-sm">Следете ги перформансите и задоволството на граѓаните во реално време.</p>
          </div>
          <div className="flex gap-2">
            {canViewFullAnalytics && (
              <>
                <Button variant="outline" size="sm" onClick={handleExportCsv} disabled={exportingCsv} aria-label="Извези податоци во CSV формат">
                  {exportingCsv ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <FileSpreadsheet className="mr-2 h-4 w-4" />}
                  Извези CSV
                </Button>
                <Button variant="outline" size="sm" onClick={handleExportPdf} disabled={exportingPdf} aria-label="Извези податоци во PDF формат">
                  {exportingPdf ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Download className="mr-2 h-4 w-4" />}
                  Извези PDF
                </Button>
              </>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" role="region" aria-label="Клучни показатели">
          {statCards.map((s) => (
            <Card key={s.label}>
              <CardContent className="py-5 space-y-2">
                <div className="flex items-center justify-between">
                  <s.icon className={`h-5 w-5 ${s.color}`} />
                </div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground font-medium">{s.label}</p>
                <p className="text-2xl font-bold text-foreground">{s.value}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="text-base">Пријави по категорија</CardTitle>
              <p className="text-xs text-muted-foreground">Дистрибуција по оддел (активни и решени наспроти вкупно)</p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={categoryChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 13%, 91%)" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="complaints" name="Пријави" fill="hsl(217, 91%, 60%)" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="resolved" name="Решени" fill="hsl(142, 71%, 45%)" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="active" name="Активни" fill="hsl(38, 92%, 50%)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Стапка на решавање</CardTitle>
              <p className="text-xs text-muted-foreground">Решени наспроти активни</p>
            </CardHeader>
            <CardContent className="flex flex-col items-center">
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie data={data.pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={80} dataKey="value" strokeWidth={0}>
                    {data.pieData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: number, name: string) => [value.toLocaleString(), name]}
                    contentStyle={{
                      borderRadius: 8,
                      border: "1px solid hsl(var(--border))",
                      backgroundColor: "hsl(var(--popover))",
                      color: "hsl(var(--popover-foreground))",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <p className="text-3xl font-bold text-foreground -mt-2">{data.resolutionRate}%</p>
              <p className="text-xs text-muted-foreground">Стапка на успешност</p>
            </CardContent>
          </Card>
        </div>

        {canViewFullAnalytics && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Месечен тренд</CardTitle>
              <p className="text-xs text-muted-foreground">Споредба меѓу пристигнати, активни и решени пријави</p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={data.monthlyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 13%, 91%)" />
                  <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="complaints" name="Пријави" stroke="hsl(217, 91%, 60%)" strokeWidth={2} dot={{ r: 3 }} />
                  <Line type="monotone" dataKey="resolved" name="Решени" stroke="hsl(142, 71%, 45%)" strokeWidth={2} dot={{ r: 3 }} />
                  <Line type="monotone" dataKey="active" name="Активни" stroke="hsl(38, 92%, 50%)" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {canViewFullAnalytics && ratingData && ratingData.length > 0 && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <CardTitle className="text-base">Задоволство на граѓаните по оддел</CardTitle>
                  <p className="text-xs text-muted-foreground">Просечна оцена (1-5 ѕвезди) врз основа на затворени пријави</p>
                </div>
                <div className="flex gap-2">
                   <Button 
                    variant={ratingSort === "desc" ? "secondary" : "outline"} 
                    size="xs" 
                    className="text-[10px] h-7 px-2"
                    onClick={() => setRatingSort("desc")}
                   >
                     Највисоки
                   </Button>
                   <Button 
                    variant={ratingSort === "asc" ? "secondary" : "outline"} 
                    size="xs" 
                    className="text-[10px] h-7 px-2"
                    onClick={() => setRatingSort("asc")}
                   >
                     Најниски
                   </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={[...ratingData]
                    .sort((a, b) => ratingSort === "desc" ? b.average_stars - a.average_stars : a.average_stars - b.average_stars)
                    .map(r => ({
                      ...r,
                      name: getCategoryMacedonianName(r.category_name)
                    }))
                  }
                  layout="vertical"
                  margin={{ left: 40, right: 40 }}
                >
                  <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="hsl(220, 13%, 91%)" />
                  <XAxis type="number" domain={[0, 5]} ticks={[0, 1, 2, 3, 4, 5]} />
                  <YAxis dataKey="name" type="category" width={120} tick={{ fontSize: 12 }} />
                  <Tooltip 
                    formatter={(value: number) => [`${value.toFixed(1)} ѕвезди`, "Просечна оцена"]}
                  />
                  <Bar 
                    dataKey="average_stars" 
                    name="Оцена" 
                    fill="hsl(45, 93%, 47%)" 
                    radius={[0, 4, 4, 0]} 
                    barSize={32}
                  />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}
      </div>
  );
}
