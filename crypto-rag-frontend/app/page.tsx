"use client";

import { color, motion } from "framer-motion";
import { Brain, Moon, Sun, Bitcoin } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { cn } from "@/lib/utils";
export default function Home() {
  const router = useRouter();
  const [isNavigating, setIsNavigating] = useState(false);

  const fadeUpVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: (i: number) => ({
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.8,
        delay: 0.3 + i * 0.2,
        ease: [0.25, 0.4, 0.25, 1] as const,
      },
    }),
  };

  const fadeOutVariants = {
    visible: { opacity: 1 },
    hidden: {
      opacity: 0,
      transition: {
        duration: 0.5,
        ease: [0.4, 0.0, 0.2, 1] as const,
      },
    },
  };

  const handleStartChatting = async () => {
    setIsNavigating(true);
    // Wait for fade-out animation to complete
    setTimeout(() => {
      router.push("/chat");
    }, 500); // Match the fade-out duration
  };

  return (
    <motion.div
      className="relative flex flex-col min-h-screen bg-white text-neutral-900 dark:text-white transition-colors duration-300 overflow-hidden"
      variants={fadeOutVariants}
      initial="visible"
      animate={isNavigating ? "hidden" : "visible"}
    >
      {/* Background Image with Blur */}
      <div className="absolute inset-0 z-0">
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{
            backgroundImage: `url("/background.jpg")`,
          }}
        />
        <div
          className="absolute inset-0 backdrop-blur-sm bg-black/30"
          style={{ backgroundColor: "rgba(20,20,20,0.75)" }}
        />
      </div>

      {/* Content Container */}
      <div className="relative z-10 flex flex-col min-h-screen">
        {/* Navbar */}
        <header className="flex justify-between items-center px-6 py-4 border-b border-white/20 backdrop-blur-md bg-white/10">
          <Link
            href="/"
            className="flex items-center gap-2 font-semibold text-lg"
          >
            <Bitcoin className="w-6 h-6 text-indigo-500" color="#f3ab24ff" />
            <span>Crypto AI</span>
          </Link>

          <nav className="hidden md:flex items-center gap-6 text-sm">
            <Link href="/about" className="hover:text-indigo-500 transition">
              About
            </Link>
            <Link href="/demo" className="hover:text-indigo-500 transition">
              Demo
            </Link>
            <Link href="/contact" className="hover:text-indigo-500 transition">
              Contact
            </Link>
          </nav>
        </header>

        {/* Main content */}
        <main className="flex-grow flex flex-col items-center justify-center text-center px-6">
          <motion.h1
            custom={0}
            variants={fadeUpVariants}
            initial="hidden"
            animate="visible"
            className="text-4xl sm:text-5xl md:text-6xl font-bold mb-4"
            style={{ letterSpacing: "6px" }}
          >
            <div>
              <Bitcoin
                className="inline-block w-16 h-16 text-indigo-500 mb-4"
                color="#f3ab24ff"
              />
              <div className="inline-block mr-2">Crypto AI</div>{" "}
            </div>
          </motion.h1>

          <motion.p
            custom={1}
            variants={fadeUpVariants}
            initial="hidden"
            animate="visible"
            className="text-lg sm:text-xl text-neutral-600 dark:text-neutral-400 mb-8"
          >
            Chat with the market of Crypto-Currency.
          </motion.p>

          <motion.div
            custom={2}
            variants={fadeUpVariants}
            initial="hidden"
            animate="visible"
          >
            <button
              onClick={handleStartChatting}
              disabled={isNavigating}
              className={cn(
                "inline-flex items-center justify-center px-6 py-3 rounded-lg text-base font-medium text-white bg-indigo-600 hover:bg-indigo-700 transition shadow-md cursor-crosshair"
              )}
            >
              Start Chatting →
            </button>
          </motion.div>
        </main>

        {/* Footer */}
        <footer className="text-center py-6 text-sm text-neutral-500 dark:text-neutral-400">
          Built by <span className="text-indigo-500">Navid Pourhadi</span>
        </footer>
      </div>
    </motion.div>
  );
}
