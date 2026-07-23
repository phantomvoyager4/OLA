import { useEffect, useRef, useState } from "react";
import { Link, NavLink } from "react-router-dom";
import OlaLogo from '../../../../data/static/logo/ola logo _3.svg';


const initialNotifications = [
  {
    id: 1,
    icon: "query_stats",
    title: "Your OLA Score is ready",
    message: "The latest match analysis has finished processing.",
    time: "2 min",
    unread: true,
    tone: "primary",
  },
  {
    id: 2,
    icon: "leaderboard",
    title: "Tier list refreshed",
    message: "The EUW Master+ snapshot now includes the latest data.",
    time: "1 hr",
    unread: true,
    tone: "secondary",
  },
  {
    id: 3,
    icon: "speed",
    title: "API capacity recovered",
    message: "Riot API capacity is back to its normal level.",
    time: "3 hr",
    unread: false,
    tone: "secondary",
  },
];

const readNotificationsStorageKey = "ola.read-notification-ids.v1";

function getInitialNotifications() {
  if (typeof window === "undefined") return initialNotifications;

  try {
    const storedValue = window.localStorage.getItem(readNotificationsStorageKey);
    const readIds = new Set(storedValue ? JSON.parse(storedValue) : []);

    return initialNotifications.map((notification) => ({
      ...notification,
      unread: notification.unread && !readIds.has(notification.id),
    }));
  } catch {
    return initialNotifications;
  }
}

export default function TopNavBar() {
  const [notifications, setNotifications] = useState(getInitialNotifications);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const notificationRef = useRef(null);
  const unreadCount = notifications.filter((notification) => notification.unread).length;

  useEffect(() => {
    try {
      const readIds = notifications
        .filter((notification) => !notification.unread)
        .map((notification) => notification.id);

      window.localStorage.setItem(
        readNotificationsStorageKey,
        JSON.stringify(readIds),
      );
    } catch {
      return undefined;
    }

    return undefined;
  }, [notifications]);

  useEffect(() => {
    if (!isNotificationsOpen) return undefined;

    const handlePointerDown = (event) => {
      if (!notificationRef.current?.contains(event.target)) {
        setIsNotificationsOpen(false);
      }
    };

    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        setIsNotificationsOpen(false);
      }
    };

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isNotificationsOpen]);

  const markAsRead = (id) => {
    setNotifications((current) =>
      current.map((notification) =>
        notification.id === id
          ? { ...notification, unread: false }
          : notification,
      ),
    );
  };

  const markAllAsRead = () => {
    setNotifications((current) =>
      current.map((notification) => ({ ...notification, unread: false })),
    );
  };

  return (
    <nav
      className="w-full h-16 flex justify-between items-center px-8 fixed top-0 z-50"
      style={{ backgroundColor: '#0a0a0a' }}
    >
      <div className="flex items-center gap-8">
        <Link
          to="/"
          aria-label="Open League Analyzer home"
          className="group flex h-16 w-12 shrink-0 items-center justify-center"
        >
          <img
            src={OlaLogo}
            alt=""
            className="block h-11 w-11 object-contain transition-transform duration-300 group-hover:scale-105"
          />
        </Link>
        <div className="hidden md:flex gap-6 items-center h-full">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `font-['Space_Grotesk'] tracking-tighter transition-colors duration-300 ${
                isActive
                  ? "text-secondary border-b-2 border-secondary pb-1"
                  : "text-on-surface-variant hover:text-secondary"
              }`
            }
          >
            Dashboard
          </NavLink>
          <NavLink
            to="/tier-list"
            className={({ isActive }) =>
              `font-['Space_Grotesk'] tracking-tighter transition-colors duration-300 ${
                isActive
                  ? "text-secondary border-b-2 border-secondary pb-1"
                  : "text-on-surface-variant hover:text-secondary"
              }`
            }
          >
            Tier list
          </NavLink>
          <NavLink
            to="/prediction"
            className={({ isActive }) =>
              `font-['Space_Grotesk'] tracking-tighter transition-colors duration-300 ${
                isActive
                  ? "text-secondary border-b-2 border-secondary pb-1"
                  : "text-on-surface-variant hover:text-secondary"
              }`
            }
          >
            Prediction
          </NavLink>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <Link to='/techstack'>
        <span className="material-symbols-outlined text-on-surface-variant cursor-pointer hover:text-secondary transition-colors pt-1.5">
          info
        </span>
        </Link>
        <div ref={notificationRef} className="relative flex items-center">
          <button
            type="button"
            aria-label={`Notifications${unreadCount ? `, ${unreadCount} unread` : ""}`}
            aria-expanded={isNotificationsOpen}
            aria-controls="notification-panel"
            aria-haspopup="dialog"
            onClick={() => setIsNotificationsOpen((current) => !current)}
            className={`notification-trigger ${isNotificationsOpen ? "is-active" : ""}`}
          >
            <span className="material-symbols-outlined">notifications</span>
            {unreadCount > 0 && (
              <span className="notification-count" aria-hidden="true">
                {unreadCount}
              </span>
            )}
          </button>

          {isNotificationsOpen && (
            <section
              id="notification-panel"
              role="dialog"
              aria-label="Notifications"
              className="notification-panel"
            >
              <div className="notification-panel-header">
                <div>
                  <p className="font-headline text-sm font-bold text-on-surface">
                    Notifications
                  </p>
                  <p className="mt-0.5 text-[11px] text-on-surface-variant">
                    {unreadCount
                      ? `${unreadCount} unread update${unreadCount === 1 ? "" : "s"}`
                      : "You’re all caught up"}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={markAllAsRead}
                  disabled={!unreadCount}
                  className="notification-read-all"
                >
                  Mark all read
                </button>
              </div>

              <div className="notification-list">
                {notifications.map((notification, index) => (
                  <button
                    key={notification.id}
                    type="button"
                    onClick={() => markAsRead(notification.id)}
                    className={`notification-item ${
                      notification.unread ? "is-unread" : ""
                    }`}
                    style={{ "--notification-index": index }}
                  >
                    <span
                      className={`notification-item-icon notification-item-icon-${notification.tone} material-symbols-outlined`}
                    >
                      {notification.icon}
                    </span>
                    <span className="min-w-0 flex-1 text-left">
                      <span className="flex items-center justify-between gap-3">
                        <span className="truncate font-headline text-xs font-bold text-on-surface">
                          {notification.title}
                        </span>
                        <span className="shrink-0 text-[10px] text-outline">
                          {notification.time}
                        </span>
                      </span>
                      <span className="mt-1 block text-[11px] leading-5 text-on-surface-variant">
                        {notification.message}
                      </span>
                    </span>
                    {notification.unread && (
                      <span className="notification-unread-dot">
                        <span className="sr-only">Unread</span>
                      </span>
                    )}
                  </button>
                ))}
              </div>

              <div className="notification-panel-footer">
                <span className="material-symbols-outlined text-[16px] text-secondary">
                  auto_awesome
                </span>
                Prototype activity feed
              </div>
            </section>
          )}
        </div>
        <span className="material-symbols-outlined text-on-surface-variant cursor-pointer hover:text-secondary transition-colors">
          settings
        </span>
        <Link to='/login'>
        <button className="bg-primary-container text-on-primary-container hover:shadow-[0_0_10px_rgba(83,238,222,0.4)] transition-all cursor-pointer duration-300 font-headline px-5 py-2 text-sm rounded-md flex items-center justify-center gap-2 active:scale-95">
          Sign In
        </button>
        </Link>
      </div>
    </nav>
  );
}
