import { User, PanelLeft, NotebookPen } from "lucide-react";
import { ChatSession } from "@/types/chat";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import {} from "lucide-react";

interface SidebarProps {
  firstName?: string;
  lastName?: string;
  isSidebarOpen: boolean;
  setIsSidebarOpen: (open: boolean) => void;
  chatSessions: ChatSession[];
  onNewChat: () => void;
  activeChatId: string | null;
  onChatSelect: (chatId: string) => void;
  isLoading?: boolean;
}

export default function Sidebar({
  firstName = "Satoshi",
  lastName = "Nakamoto",
  isSidebarOpen = false,
  setIsSidebarOpen,
  chatSessions,
  onNewChat,
  activeChatId,
  onChatSelect,
  isLoading = false,
}: SidebarProps) {
  const router = useRouter();
  const [showDetail, setDetail] = useState(false);

  useEffect(() => {
    if (isSidebarOpen) {
      // Delay showing text until sidebar animation completes (200ms + small buffer)
      const timer = setTimeout(() => {
        setDetail(true);
      }, 200);
      return () => clearTimeout(timer);
    } else {
      // Hide text immediately when sidebar starts closing
      setDetail(false);
    }
  }, [isSidebarOpen]);

  return (
    <>
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-[#181818] z-10 lg:hidden"
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
        />
      )}

      <div
        className={`
        fixed lg:static h-screen 
        ${
          isSidebarOpen
            ? "w-64 bg-[#181818]"
            : "w-16 bg-[#212121] border-r border-[#383838]"
        } 
        transition-all duration-200 ease-in-out
        flex flex-col z-50 text-sm
        ${isSidebarOpen ? "overflow-y-auto" : ""}
      `}
      >
        <div className="p-4 flex items-center justify-between">
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="cursor-e-resize hover:bg-[#383838] rounded-full p-2 cursor-e-resize transition-colors"
          >
            {isSidebarOpen ? (
              <PanelLeft size={20} color="#ccc" />
            ) : (
              <PanelLeft size={20} color="#ccc" />
            )}
          </button>
        </div>

        <button
          onClick={onNewChat}
          className={`
            ${
              isSidebarOpen
                ? "m-4 p-2 flex items-center gap-2 hover:text-gray-100 hover:bg-[#383838] text-gray-200 rounded-lg cursor-crosshair"
                : "m-4 text-gray-400 hover:text-gray-600  hover:bg-[#383838] rounded-full p-2 w-9 h-9 flex items-center justify-center cursor-crosshair"
            }
          `}
        >
          <NotebookPen size={20} color="#ccc" />
          {isSidebarOpen && showDetail && (
            <span className="opacity-0 animate-fade-in opacity-100 transition-opacity duration-300">
              New Chat
            </span>
          )}
        </button>
        {isSidebarOpen && showDetail && (
          <div className="flex-1 overflow-y-auto min-h-0">
            {isLoading ? (
              <div className="flex items-center justify-center h-20 text-gray-400">
                Loading chats...
              </div>
            ) : chatSessions.length === 0 ? (
              <div className="flex items-center justify-center h-20 text-gray-400">
                No chats yet
              </div>
            ) : (
              chatSessions?.map((chat) => (
                <div
                  key={chat.id}
                  className={`
                  p-4 hover:bg-gray-800 cursor-pointer border-b border-gray-800
                  ${!isSidebarOpen && "hidden"}
                  ${activeChatId === chat.id ? "bg-gray-700" : ""}
                `}
                  onClick={() => onChatSelect(chat.id)}
                >
                  <div className="flex items-center gap-3">
                    <div className="flex-1 opacity-0 animate-fade-in opacity-100 transition-opacity duration-200">
                      <p className="text-gray-200 truncate">{chat.title}</p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
        {isSidebarOpen && showDetail && (
          <div className="p-4 border-t border-gray-800">
            <button
              // onClick={handleDashboardClick}
              className="text-gray-200 font-medium hover:text-white transition-colors"
            >
              <div
                className={`flex items-center gap-3 ${
                  !isSidebarOpen && "hidden"
                } cursor-pointer`}
              >
                <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center">
                  <User size={20} className="text-gray-300" />
                </div>

                <span className="opacity-0 animate-fade-in opacity-100 transition-opacity duration-200">
                  {firstName} {lastName}
                </span>
              </div>
            </button>
          </div>
        )}
      </div>
    </>
  );
}
