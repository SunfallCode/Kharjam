import React, { useState, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { DashboardIcon } from "@/assets/icons/DashboardIcon";
import { UserIcon } from "@/assets/icons/UserIcon";
import { BellIcon } from "@/assets/icons/BellIcon";
import { DollarIcon } from "@/assets/icons/DollarIcon";
import { UsersIcon } from "@/assets/icons/UsersICon";

function BottomBar() {
  const pathname = usePathname();
  const router = useRouter();
  const [selected, setSelected] = useState("");

  const pathToNavId: Record<string, string> = {
    "/panel/dashboard": "Home",
    "/panel/profile": "profile",
    "/panel/group": "groups",
  };

  const navIdToPath: Record<string, string> = {
    "Home": "/panel/dashboard",
    "profile": "/panel/profile",
    "groups": "/panel/group",
  };

  useEffect(() => {
    const activeId = pathToNavId[pathname] || "";
    setSelected(activeId);
  }, [pathname]);

  const navItems = [
    {
      id: "finance",
      label: "finance",
      icon: <DollarIcon className="w-6 h-6" />,
    },
    { id: "groups", label: "groups", icon: <UsersIcon className="w-6 h-6" /> },
    { id: "Home", label: "Home", icon: <DashboardIcon className="w-6 h-6" /> },
    {
      id: "notifications",
      label: "notification",
      icon: <BellIcon className="w-6 h-6" />,
    },
    { id: "profile", label: "Profile", icon: <UserIcon className="w-6 h-6" /> },
  ];
  return (
    <div className="fixed bottom-0 w-full h-26 bg-transparent pointer-events-none">
      <div className="fixed inset-x-0 bottom-0 h-16 bg-back shadow-lg pointer-events-auto rounded-t-3xl">
        <div className="relative h-full flex items-center justify-around">
          {navItems.map((item) => {
            const isSel = selected === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  const path = navIdToPath[item.id];
                  if (path) {
                    router.push(path);
                  }
                  setSelected(item.id);
                }}
                className={cn(
                  "relative flex flex-col items-center justify-center transition-all",
                  isSel
                    ? "border-t-2 bg-back border-sky-400 text-sky-400 font-semibold w-[86px] h-[86px] rounded-full"
                    : "text-gray-500 hover:text-primary-500 w-12 h-12 hover:-translate-y-1"
                )}
              >
                {item.icon}
                <p>{item.label}</p>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default BottomBar;
