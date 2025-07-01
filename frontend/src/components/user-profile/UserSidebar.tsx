"use client";
import { useTranslation } from "@/contexts/TranslationContext";
import React from "react";
import { useDispatch } from "react-redux";
import { useRouter } from "next/navigation";
import { logout as logoutUser } from '@/redux/slices/authSlice';
import { logoutAction } from "@/actions/auth";

interface UserSidebarProps {
  active: string;
  onNavigate: (section: string) => void;
}

export default function UserSidebar({ active, onNavigate }: UserSidebarProps) {
  const { t } = useTranslation();
  const dispatch = useDispatch();
  const router = useRouter();

  const handleLogout = async () => {
    dispatch(logoutUser());
    await logoutAction();
    router.refresh();
  };

  const sections = [
    { key: "profile", label: t('userSidebar.profile') },
    { key: "settings", label: t('userSidebar.settings') },
    { key: "logout", label: t('userSidebar.logout') },
  ];
  return (
    <aside className="w-full md:w-64 bg-white/80 dark:bg-gray-900/80 rounded-lg shadow-lg p-6 flex flex-col gap-2">
      {sections.map((section) => (
        <button
          key={section.key}
          className={`text-left px-4 py-2 rounded-lg transition-colors cursor-pointer ${
            active === section.key
              ? "bg-blue-500 text-white"
              : "hover:bg-gray-200 dark:hover:bg-gray-800 text-gray-900 dark:text-white"
          }`}
          onClick={
            section.key === "logout"
              ? handleLogout
              : () => onNavigate(section.key)
          }
        >
          {section.label}
        </button>
      ))}
    </aside>
  );
}
