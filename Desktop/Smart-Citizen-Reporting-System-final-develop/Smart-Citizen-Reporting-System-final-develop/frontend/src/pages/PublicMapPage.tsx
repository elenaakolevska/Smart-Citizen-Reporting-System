import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AppLayout } from "@/components/AppLayout";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { fetchReports, type ReportRead } from "@/services/reports";
import { useLookups } from "@/hooks/useLookups";
import { deriveTitle, formatDate, getPriorityLabel, getPriorityStyle, getStatusStyle, getCategoryMacedonianName } from "@/lib/reportHelpers";
import { useNavigate } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Map as MapIcon, Filter } from "lucide-react";

// Fix default marker icon
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

// Custom colored markers for statuses
const getMarkerIcon = (statusId: number | null) => {
  let color = "#3b82f6"; // blue (default/new)
  if (statusId === 2) color = "#eab308"; // warning (in progress)
  if (statusId === 3) color = "#22c55e"; // success (resolved)
  if (statusId === 4) color = "#ef4444"; // destructive (rejected)
  
  return new L.DivIcon({
    className: "custom-div-icon",
    html: `<div style="background-color: ${color}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 4px rgba(0,0,0,0.3);"></div>`,
    iconSize: [12, 12],
    iconAnchor: [6, 6],
  });
};

export default function PublicMapPage() {
  const navigate = useNavigate();
  const { categories, statuses, categoryLabel, statusLabel } = useLookups();
  const [statusFilter, setStatusFilter] = useState("all");
  const [categoryFilter, setCategoryFilter] = useState("all");

  const { data: reports = [], isLoading } = useQuery({
    queryKey: ["reports", "all-public"],
    queryFn: fetchReports, // In a real app, this might be a dedicated public endpoint
  });

  const filteredReports = reports.filter((r) => {
    if (r.latitude == null || r.longitude == null) return false;
    const matchStatus = statusFilter === "all" || String(r.status_id) === statusFilter;
    const matchCategory = categoryFilter === "all" || String(r.category_id) === categoryFilter;
    return matchStatus && matchCategory;
  });

  return (
    <AppLayout>
      <div className="h-[calc(100vh-8rem)] flex flex-col gap-4">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <MapIcon className="h-6 w-6 text-primary" /> Интерактивна мапа
            </h1>
            <p className="text-sm text-muted-foreground">Преглед на сите пријавени проблеми во градот.</p>
          </div>
          
          <Card className="w-full sm:w-auto">
            <CardContent className="p-2 flex flex-wrap gap-2 items-center">
              <Filter className="h-4 w-4 text-muted-foreground ml-2" />
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[140px] h-9 text-xs"><SelectValue placeholder="Статус" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Сите статуси</SelectItem>
                  {statuses.map((s) => (
                    <SelectItem key={s.id} value={String(s.id)}>{s.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger className="w-[160px] h-9 text-xs"><SelectValue placeholder="Категорија" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Сите категории</SelectItem>
                  {categories.map((c) => (
                    <SelectItem key={c.id} value={String(c.id)}>{getCategoryMacedonianName(c.name)}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </CardContent>
          </Card>
        </div>

        <div className="flex-1 rounded-xl overflow-hidden border border-border relative z-0">
          <MapContainer center={[41.9981, 21.4254]} zoom={13} style={{ height: "100%", width: "100%" }}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {filteredReports.map((r) => (
              <Marker 
                key={r.id} 
                position={[r.latitude!, r.longitude!]} 
                icon={getMarkerIcon(r.status_id)}
              >
                <Popup className="custom-popup">
                  <div className="p-1 space-y-2 min-w-[200px]">
                    <div className="flex justify-between items-start gap-2">
                      <h3 className="font-bold text-sm leading-tight">{deriveTitle(r.description)}</h3>
                      <Badge className={`${getStatusStyle(r.status_id)} text-[10px] px-1.5 py-0 h-4`}>
                        {statusLabel(r.status_id)}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground line-clamp-2">{r.description}</p>
                    <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-4">
                      {categoryLabel(r.category_id)}
                    </Badge>
                    <div className="flex items-center justify-start">
                      <Badge variant="outline" className={`${getPriorityStyle(r.priority)} text-[10px] px-1.5 py-0 h-4`}>
                        {getPriorityLabel(r.priority)}
                      </Badge>
                    </div>
                    <div className="flex justify-between items-center pt-1">
                      <span className="text-[10px] text-muted-foreground">{formatDate(r.created_at)}</span>
                      <Button variant="link" size="sm" className="h-auto p-0 text-xs" onClick={() => navigate(`/complaints/${r.id}`)}>
                        Детали
                      </Button>
                    </div>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>
          
          <div className="absolute bottom-4 left-4 bg-background/90 backdrop-blur-sm p-3 rounded-lg border border-border shadow-lg z-[1000] text-xs space-y-2">
            <p className="font-semibold border-bottom pb-1 mb-1">Легенда:</p>

            <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-blue-500 border border-white" /> Активен</div>
            <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-yellow-500 border border-white" /> Решен</div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
