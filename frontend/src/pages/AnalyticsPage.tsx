import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AppLayout } from "@/components/AppLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { TrendingUp, FileText, CheckCircle, Clock, Users, Download, FileJson, FileSpreadsheet, Loader2 } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, Legend } from "recharts";
import { fetchAnalyticsSummary, exportToCsv, exportToPdf } from "@/services/analytics";
import { useToast } from "@/hooks/use-toast";

const COLORS = ["hsl(142, 71%, 45%)", "hsl(220, 13%, 91%)"];

export default function AnalyticsPage() {
  const { toast } = useToast();
  const [exportingCsv, setExportingCsv] = useState(false);
  const [exportingPdf, setExportingPdf] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ["analytics", "summary"],
    queryFn: fetchAnalyticsSummary,
  });

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
      <AppLayout>
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
      </AppLayout>
    );
  }

  if (error || !data) {
    return (
      <AppLayout>
        <div className="text-center py-12 text-destructive">
          <p className="font-semibold">Грешка при вчитување на аналитиката.</p>
          <Button variant="outline" className="mt-4" onClick={() => window.location.reload()}>Обиди се повторно</Button>
        </div>
      </AppLayout>
    );
  }

  const statCards = [
    { label: "ВКУПНО ПРИЈАВИ", value: data.kpis.total, icon: FileText, trend: "+12.5%", color: "text-primary" },
    { label: "РЕШЕНИ СЛУЧАИ", value: data.kpis.resolved, icon: CheckCircle, trend: "+8.2%", color: "text-success" },
    { label: "ПРОСЕЧНО ВРЕМЕ", value: data.kpis.avgTime, icon: Clock, trend: "-1.1 ден", color: "text-warning" },
    { label: "АКТИВНИ ГРАЃАНИ", value: data.kpis.activeCitizens.toLocaleString(), icon: Users, trend: "+5.4%", color: "text-info" },
  ];

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Аналитички преглед</h1>
            <p className="text-muted-foreground text-sm">Следете ги перформансите и задоволството на граѓаните во реално време.</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleExportCsv} disabled={exportingCsv}>
              {exportingCsv ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <FileSpreadsheet className="mr-2 h-4 w-4" />}
              Извези CSV
            </Button>
            <Button variant="outline" size="sm" onClick={handleExportPdf} disabled={exportingPdf}>
              {exportingPdf ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Download className="mr-2 h-4 w-4" />}
              Извези PDF
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {statCards.map((s) => (
            <Card key={s.label}>
              <CardContent className="py-5 space-y-2">
                <div className="flex items-center justify-between">
                  <s.icon className={`h-5 w-5 ${s.color}`} />
                  <span className="text-xs font-medium text-success flex items-center gap-0.5">
                    <TrendingUp className="h-3 w-3" /> {s.trend}
                  </span>
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
              <p className="text-xs text-muted-foreground">Дистрибуција по оддел (решени наспроти вкупно)</p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={data.categoryData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 13%, 91%)" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="complaints" name="Пријави" fill="hsl(217, 91%, 60%)" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="resolved" name="Решени" fill="hsl(142, 71%, 45%)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Задоволство по оддел</CardTitle>
              <p className="text-xs text-muted-foreground">Просечна оценка (1-5 ѕвезди)</p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={data.ratingData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" domain={[0, 5]} hide />
                  <YAxis dataKey="name" type="category" tick={{ fontSize: 10 }} width={100} />
                  <Tooltip 
                    formatter={(value: number) => [`${value} / 5`, 'Оценка']}
                    contentStyle={{ fontSize: '12px' }}
                  />
                  <Bar dataKey="rating" name="Оценка" fill="hsl(45, 93%, 47%)" radius={[0, 4, 4, 0]} barSize={20} />
                </BarChart>
              </ResponsiveContainer>
              <div className="mt-2 text-center">
                <p className="text-xs text-muted-foreground italic">Врз основа на {data.ratingData.reduce((acc, curr) => acc + curr.count, 0)} оценки</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Стапка на решавање</CardTitle>
              <p className="text-xs text-muted-foreground">Решени наспроти нерешени</p>
            </CardHeader>
            <CardContent className="flex flex-col items-center">
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie data={data.pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={80} dataKey="value" strokeWidth={0}>
                    {data.pieData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <p className="text-3xl font-bold text-foreground -mt-2">{data.resolutionRate}%</p>
              <p className="text-xs text-muted-foreground">Стапка на успешност</p>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Месечен тренд</CardTitle>
            <p className="text-xs text-muted-foreground">Споредба меѓу пристигнати пријави и решени случаи</p>
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
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
