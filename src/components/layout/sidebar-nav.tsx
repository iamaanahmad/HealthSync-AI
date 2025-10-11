"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
} from "@/components/ui/sidebar";
import { Icons } from "@/components/icons";
import {
  ShieldCheck,
  FlaskConical,
  Activity,
  FileJson,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const navItems = [
  {
    href: "/dashboard",
    icon: ShieldCheck,
    label: "Patient Dashboard",
  },
  {
    href: "/researcher",
    icon: FlaskConical,
    label: "Researcher Portal",
  },
  {
    href: "/monitor",
    icon: Activity,
    label: "Agent Monitor",
  },
  {
    href: "/metta-explorer",
    icon: FileJson,
    label: "MeTTa Explorer",
  },
];

export function SidebarNav() {
  const pathname = usePathname();

  return (
    <Sidebar>
      <SidebarContent>
        <SidebarHeader>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" className="h-9 w-9" asChild>
              <Link href="/">
                <Icons.Logo className="w-6 h-6 text-primary" />
              </Link>
            </Button>
            <span className="text-lg font-semibold font-headline">HealthSync AI</span>
          </div>
        </SidebarHeader>
        <SidebarMenu>
          {navItems.map((item) => (
            <SidebarMenuItem key={item.href}>
              <SidebarMenuButton
                asChild
                isActive={pathname.startsWith(item.href)}
                tooltip={{ children: item.label }}
              >
                <Link href={item.href}>
                  <item.icon />
                  <span>{item.label}</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarContent>
    </Sidebar>
  );
}
