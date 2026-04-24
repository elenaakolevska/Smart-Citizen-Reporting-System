import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AppLayout } from "@/components/AppLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Bell, Mail, Shield, User } from "lucide-react";
import { fetchUserSettings, updateUserSettings } from "@/services/users";
import { toast } from "sonner";

export default function SettingsPage() {
  const queryClient = useQueryClient();

  const { data: settings, isLoading } = useQuery({
    queryKey: ["user-settings"],
    queryFn: fetchUserSettings,
  });

  const mutation = useMutation({
    mutationFn: updateUserSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["user-settings"] });
      toast.success("Поставките се успешно ажурирани.");
    },
    onError: () => {
      toast.error("Грешка при ажурирање на поставките.");
    },
  });

  const handleToggleEmail = (checked: boolean) => {
    mutation.mutate({ email_notifications: checked });
  };

  return (
    <AppLayout>
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Поставки</h1>
          <p className="text-muted-foreground text-sm">
            Управувајте со вашиот профил и преференции за нотификации.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-1 space-y-4">
            <Card className="p-2">
              <nav className="space-y-1">
                <button className="w-full flex items-center gap-3 px-3 py-2 text-sm font-medium bg-primary/10 text-primary rounded-md">
                  <Bell className="h-4 w-4" /> Нотификации
                </button>
                <button className="w-full flex items-center gap-3 px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-secondary rounded-md transition-colors">
                  <User className="h-4 w-4" /> Профил
                </button>
                <button className="w-full flex items-center gap-3 px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-secondary rounded-md transition-colors">
                  <Shield className="h-4 w-4" /> Безбедност
                </button>
              </nav>
            </Card>
          </div>

          <div className="md:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Mail className="h-5 w-5" /> Е-маил известувања
                </CardTitle>
                <CardDescription>
                  Изберете кога сакате да добивате пораки на вашата е-маил адреса.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between space-x-4">
                  <div className="flex-1 space-y-1">
                    <Label htmlFor="email-notif" className="text-base font-semibold">
                      Ажурирања на пријави
                    </Label>
                    <p className="text-sm text-muted-foreground">
                      Добивајте известувања кога статусот на вашата пријава ќе се промени.
                    </p>
                  </div>
                  {isLoading ? (
                    <Skeleton className="h-6 w-10" />
                  ) : (
                    <Switch
                      id="email-notif"
                      checked={settings?.email_notifications}
                      onCheckedChange={handleToggleEmail}
                      disabled={mutation.isPending}
                    />
                  )}
                </div>

                <div className="flex items-center justify-between space-x-4 opacity-50">
                  <div className="flex-1 space-y-1">
                    <Label className="text-base font-semibold">
                      Месечен извештај
                    </Label>
                    <p className="text-sm text-muted-foreground">
                      Месечен преглед на активноста во вашата општина.
                    </p>
                  </div>
                  <Switch disabled checked={false} />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Ин-ап нотификации</CardTitle>
                <CardDescription>
                  Известувања кои се појавуваат додека ја користите апликацијата.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between space-x-4">
                  <div className="flex-1 space-y-1">
                    <Label className="text-base">Звучни известувања</Label>
                  </div>
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center justify-between space-x-4">
                  <div className="flex-1 space-y-1">
                    <Label className="text-base">Push нотификации</Label>
                  </div>
                  <Switch defaultChecked />
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
