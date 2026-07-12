"use client";

import React, { useState, useEffect, useRef } from "react";
import { 
  MessageSquare, 
  BookOpen, 
  BarChart3, 
  Sparkles, 
  FileText, 
  Send, 
  Trash2, 
  AlertTriangle, 
  RefreshCw,
  Users,
  Compass,
  AlertOctagon,
  Scale
} from "lucide-react";

// Define TypeScript interfaces for our application state
interface Message {
  role: "user" | "assistant";
  content: string;
  detected_conflict?: boolean;
}

interface RawLaw {
  id: string;
  title: string;
  content: string;
}

interface ChatResponse {
  session_id: string;
  original_query: string;
  rewritten_query: string;
  response: string;
  raw_laws: RawLaw[];
  is_out_of_scope: boolean;
  detected_conflict: boolean;
}

interface StatItem {
  original_query: string;
  count: number;
}

interface AdminStats {
  total_sessions: number;
  total_interactions: number;
  total_out_of_scope: number;
  total_conflicts: number;
  top_faq: StatItem[];
  top_out_of_scope: StatItem[];
}

export default function Home() {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

  // --- View States ---
  const [activeTab, setActiveTab] = useState<"chat" | "admin">("chat");

  // --- Chat States ---
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "สวัสดีครับเจ้าหน้าที่สรรพากร ยินดีต้อนรับสู่ระบบคลังความรู้การจดทะเบียนภาษีมูลค่าเพิ่ม (VAT Registration RAG) ท่านสามารถสอบถามข้อกฎหมาย ขั้นตอน เอกสาร หรือระเบียบที่เกี่ยวข้องกับการจดทะเบียน VAT ได้ทันทีครับ"
    }
  ]);
  const [query, setQuery] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [injectedLaws, setInjectedLaws] = useState<RawLaw[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // --- Admin Stats States ---
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [recentLogs, setRecentLogs] = useState<any[]>([]);
  const [lawsList, setLawsList] = useState<any[]>([]);
  const [statsLoading, setStatsLoading] = useState(false);

  // --- Accessibility Font Size States ---
  // Font scale levels: 0 (Small - 14px), 1 (Normal/Default - 16px), 2 (Large - 18px), 3 (Extra Large - 22px)
  const [fontScale, setFontScale] = useState<number>(1);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll chat to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Generate unique session ID on mount
  useEffect(() => {
    const randomSess = "sess_" + Date.now().toString(36) + Math.random().toString(36).substring(2, 5);
    setSessionId(randomSess);
  }, []);

  // Fetch admin stats if the admin panel is visited
  const fetchStats = async () => {
    setStatsLoading(true);
    try {
      // 1. Fetch Stats summary
      const resStats = await fetch(`${API_BASE_URL}/api/stats`);
      if (resStats.ok) {
        const data = await resStats.json();
        setStats(data);
      }
      
      // 2. Fetch Recent Log list
      const resLogs = await fetch(`${API_BASE_URL}/api/logs?limit=15`);
      if (resLogs.ok) {
        const dataLogs = await resLogs.json();
        setRecentLogs(dataLogs);
      }
      
      // 3. Fetch Laws Vector Store index
      const resLaws = await fetch(`${API_BASE_URL}/api/laws`);
      if (resLaws.ok) {
        const dataLaws = await resLaws.json();
        setLawsList(dataLaws);
      }

      setErrorMsg(null);
    } catch (err) {
      console.error(err);
      setErrorMsg("กรุณาเปิดการทำงานของ FastAPI Backend (Port 8000) ก่อนใช้งาน");
    } finally {
      setStatsLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "admin") {
      fetchStats();
    }
  }, [activeTab]);

  // --- Accessibility Font Size Styling Mapping ---
  // These mapping configurations determine Tailwind font sizes based on the user's active zoom level.
  // This satisfies the constraint to provide A+ / A- buttons that affect the chat bubbles and the legal panel text.
  const getChatFontSize = (): string => {
    switch (fontScale) {
      case 0: return "text-xs md:text-sm"; // Small
      case 2: return "text-base md:text-lg"; // Large
      case 3: return "text-lg md:text-xl";  // Extra Large
      default: return "text-sm md:text-base"; // Normal
    }
  };

  const getLawFontSize = (): string => {
    switch (fontScale) {
      case 0: return "text-xs md:text-xs";
      case 2: return "text-sm md:text-base";
      case 3: return "text-base md:text-lg";
      default: return "text-xs md:text-sm";
    }
  };

  // Adjust zoom handlers
  const zoomIn = () => {
    if (fontScale < 3) setFontScale(prev => prev + 1);
  };

  const zoomOut = () => {
    if (fontScale > 0) setFontScale(prev => prev - 1);
  };

  // Handle message sending
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;

    const userMessageText = query.trim();
    setQuery("");
    setErrorMsg(null);

    // Append user question
    const updatedMessages = [...messages, { role: "user" as const, content: userMessageText }];
    setMessages(updatedMessages);
    setIsLoading(true);

    try {
      // Build request body including context history for Query Re-writing
      // We filter out greeting message so history contains only real user-assistant pairs
      const historyPayload = updatedMessages
        .slice(1, -1) // skip the greeting (index 0) and the current prompt (which was just added at the end)
        .map(msg => ({
          role: msg.role,
          content: msg.content
        }));

      const res = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          query: userMessageText,
          history: historyPayload
        })
      });

      if (!res.ok) {
        throw new Error("ระบบเชื่อมต่อ API ล้มเหลว");
      }

      const data: ChatResponse = await res.json();

      // Append backend RAG response
      setMessages(prev => [...prev, { 
        role: "assistant", 
        content: data.response,
        detected_conflict: data.detected_conflict
      }]);

      // Inject raw laws in the right-side split screen
      if (data.raw_laws && data.raw_laws.length > 0) {
        setInjectedLaws(data.raw_laws);
      } else if (data.is_out_of_scope) {
        // Keep existing laws or clear if out of scope
        setInjectedLaws([]);
      }

    } catch (err) {
      console.error(err);
      setErrorMsg("ไม่สามารถส่งข้อมูลไปยัง RAG Backend ได้ กรุณาตรวจสอบการรันเซิร์ฟเวอร์");
      // Remove the last user message as it failed to process
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
    }
  };

  // Reset Session History
  const handleClearSession = async () => {
    if (isLoading) return;
    try {
      await fetch(`${API_BASE_URL}/api/clear`, { method: "POST" });
    } catch (err) {
      console.error("Failed to clear backend logs:", err);
    }
    const randomSess = "sess_" + Date.now().toString(36) + Math.random().toString(36).substring(2, 5);
    setSessionId(randomSess);
    setInjectedLaws([]);
    setMessages([
      {
        role: "assistant",
        content: "เริ่มบทสนทนาใหม่แล้วครับ ท่านสามารถถามคำถามเกี่ยวกับหลักเกณฑ์การจดทะเบียน VAT ได้เลยครับ"
      }
    ]);
    setErrorMsg(null);
  };

  // Reset all SQLite logs (Demo feature)
  const handleResetDatabaseLogs = async () => {
    if (confirm("คุณต้องการล้างข้อมูลประวัติและสถิติทั้งหมดในระบบหลังบ้านใช่หรือไม่?")) {
      try {
        const res = await fetch(`${API_BASE_URL}/api/clear`, { method: "POST" });
        if (res.ok) {
          fetchStats();
          alert("ล้างฐานข้อมูลประวัติเรียบร้อยแล้ว (ระบบทำการเริ่มข้อมูลเริ่มต้นให้ใหม่)");
        }
      } catch (err) {
        alert("ไม่สามารถรีเซ็ตฐานข้อมูลได้");
      }
    }
  };

  return (
    <div className="flex flex-col min-height-screen h-screen bg-[#F4F7FC]">
      
      {/* --- HEADER BAR --- */}
      <header className="bg-gov-navy text-white px-6 py-4 shadow-premium flex flex-wrap items-center justify-between z-10">
        
        {/* Ministry/Department Brand Logo with detailed SVG emblem */}
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab("chat")}>
          <div className="bg-white p-1.5 rounded-full flex items-center justify-center shadow-md">
            <svg width="34" height="34" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" className="text-gov-navy">
              <circle cx="50" cy="50" r="45" stroke="#0F2C59" strokeWidth="8" fill="#F0F4F8"/>
              <path d="M50 15 L80 40 L68 40 L68 80 L32 80 L32 40 L20 40 Z" fill="#0F2C59"/>
              <path d="M50 30 L60 45 L50 60 L40 45 Z" fill="#D4A373"/>
              <line x1="50" y1="60" x2="50" y2="80" stroke="#FFFFFF" strokeWidth="4"/>
            </svg>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="bg-gov-gold text-gov-navy text-xs font-semibold px-2 py-0.5 rounded-full">
                NIDA MADT IS
              </span>
              <span className="text-[10px] text-gray-300 tracking-wider">ON-PREMISE AI SYSTEM</span>
            </div>
            <h1 className="text-base md:text-lg font-bold leading-tight">
              ระบบสืบค้นข้อกฎหมายการจดทะเบียนภาษีมูลค่าเพิ่ม (VAT RAG)
            </h1>
          </div>
        </div>

        {/* Navigation Tab toggler + Accessibility Zoom scale control */}
        <div className="flex items-center space-x-6 mt-2 sm:mt-0">
          
          {/* Tab Navigation */}
          <nav className="flex space-x-2 bg-[#173e75] p-1 rounded-lg">
            <button 
              id="btn-chat-view"
              onClick={() => setActiveTab("chat")}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs md:text-sm font-medium transition-all ${
                activeTab === "chat" 
                  ? "bg-white text-gov-navy shadow-sm" 
                  : "text-gray-200 hover:text-white hover:bg-gov-navy/40"
              }`}
            >
              <MessageSquare className="w-4 h-4" />
              <span>ระบบสืบค้น (User QA)</span>
            </button>
            <button 
              id="btn-admin-view"
              onClick={() => setActiveTab("admin")}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs md:text-sm font-medium transition-all ${
                activeTab === "admin" 
                  ? "bg-white text-gov-navy shadow-sm" 
                  : "text-gray-200 hover:text-white hover:bg-gov-navy/40"
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              <span>แดชบอร์ด (Admin Panel)</span>
            </button>
          </nav>

          {/* Accessibility Font Size Control Panel (A- / A+) */}
          {/* Satisfies the requirement: dynamic resizing for user accessibility */}
          <div className="flex items-center bg-[#173e75] rounded-lg p-1 space-x-1">
            <button
              onClick={zoomOut}
              disabled={fontScale === 0}
              className={`w-8 h-8 rounded flex items-center justify-center text-xs font-bold transition-all ${
                fontScale === 0 
                  ? "text-gray-400 cursor-not-allowed opacity-50" 
                  : "bg-gov-navy text-white hover:bg-gov-blue"
              }`}
              title="ลดขนาดตัวอักษร (A-)"
            >
              A-
            </button>
            <span className="text-xs px-1 font-semibold text-gray-200">
              {fontScale === 0 ? "เล็ก" : fontScale === 1 ? "ปกติ" : fontScale === 2 ? "ใหญ่" : "ใหญ่พิเศษ"}
            </span>
            <button
              onClick={zoomIn}
              disabled={fontScale === 3}
              className={`w-8 h-8 rounded flex items-center justify-center text-xs font-bold transition-all ${
                fontScale === 3 
                  ? "text-gray-400 cursor-not-allowed opacity-50" 
                  : "bg-gov-navy text-white hover:bg-gov-blue"
              }`}
              title="เพิ่มขนาดตัวอักษร (A+)"
            >
              A+
            </button>
          </div>

        </div>
      </header>

      {/* --- ERROR BAR --- */}
      {errorMsg && (
        <div className="bg-red-50 border-b border-red-200 text-red-800 px-6 py-2.5 flex items-center space-x-2 text-xs md:text-sm animate-fade-in font-medium">
          <AlertTriangle className="w-4.5 h-4.5 text-red-600 flex-shrink-0" />
          <span>{errorMsg}</span>
          <button 
            className="underline ml-auto hover:text-red-900" 
            onClick={() => {
              setErrorMsg(null);
              if (activeTab === "admin") fetchStats();
            }}
          >
            โหลดใหม่
          </button>
        </div>
      )}

      {/* --- MAIN CORE PANEL --- */}
      <main className="flex-1 overflow-hidden flex flex-col">
        
        {/* TAB 1: SPLIT SCREEN CHAT & LAW REFERENCE */}
        {activeTab === "chat" && (
          <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
            
            {/* LEFT VIEWPORT: CHAT CONVERSATION */}
            <section className="flex-1 flex flex-col bg-white border-r border-gray-200 md:w-3/5">
              
              {/* Top Banner Left Panel */}
              <div className="px-6 py-3 bg-gov-light border-b border-gray-200 flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Sparkles className="w-4 h-4 text-gov-blue animate-pulse" />
                  <span className="text-xs font-semibold text-gov-navy">
                    บทสนทนาถาม-ตอบกฎหมายภาษี (ประมวลผลโลคอล)
                  </span>
                </div>
                <button 
                  onClick={handleClearSession}
                  className="text-gray-500 hover:text-red-600 flex items-center space-x-1 text-xs py-1 px-2 rounded hover:bg-red-50 transition-all font-medium"
                  title="เริ่มบทสนทนาใหม่เพื่อรีเซ็ตบริบทความจำ"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>เริ่มเซสชันใหม่</span>
                </button>
              </div>

              {/* Chat Thread Container */}
              {/* Inherits class computed by Accessibility dynamic scale state */}
              <div className={`flex-1 overflow-y-auto p-6 space-y-4 ${getChatFontSize()}`}>
                {messages.map((msg, index) => (
                  <div 
                    key={index}
                    className={`flex flex-col max-w-[85%] ${
                      msg.role === "user" 
                        ? "ml-auto items-end" 
                        : "mr-auto items-start"
                    } animate-fade-in`}
                  >
                    {/* Sender Indicator */}
                    <span className="text-[10px] text-gray-400 mb-1 px-1 font-medium">
                      {msg.role === "user" ? "คุณ (เจ้าหน้าที่สรรพากร)" : "ระบบผู้ช่วยกฎหมาย AI RAG"}
                    </span>

                    {/* Chat Bubble */}
                    <div 
                      className={`p-4 rounded-2xl shadow-sm border ${
                        msg.role === "user" 
                          ? "bg-gov-navy text-white border-gov-navy rounded-tr-none" 
                          : "bg-gov-light/50 text-gov-navy border-gray-200 rounded-tl-none"
                      } leading-relaxed whitespace-pre-wrap`}
                    >
                      {/* Highlighted Warning Box if a regulatory conflict is flagged */}
                      {msg.detected_conflict && (
                        <div className="mb-3 bg-amber-50 border border-gov-gold text-amber-900 text-xs md:text-sm p-3 rounded-lg flex items-start space-x-2 animate-pulse-border">
                          <AlertTriangle className="w-4 h-4 text-gov-gold flex-shrink-0 mt-0.5" />
                          <div>
                            <span className="font-semibold text-gov-navy block">ข้อขัดแย้งของระเบียบกฎหมายหน้างาน!</span>
                            <span className="text-gray-700">ตรวจพบลักษณะคำสั่งหรือข้อบังคับที่ขัดแย้งกันในการยื่นคำขอ โปรดศึกษารายละเอียดคำเตือนข้อควรระวัง</span>
                          </div>
                        </div>
                      )}
                      
                      {msg.content}
                    </div>
                  </div>
                ))}

                {/* Loading state indicator */}
                {isLoading && (
                  <div className="flex flex-col items-start max-w-[80%] animate-pulse">
                    <span className="text-[10px] text-gray-400 mb-1 px-1 font-medium">ระบบกำลังวิเคราะห์และสืบค้นข้อระเบียบ...</span>
                    <div className="bg-gov-light/30 border border-gray-100 p-4 rounded-2xl rounded-tl-none flex items-center space-x-2">
                      <div className="w-2 h-2 bg-gov-blue rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gov-blue rounded-full animate-bounce [animation-delay:0.2s]"></div>
                      <div className="w-2 h-2 bg-gov-blue rounded-full animate-bounce [animation-delay:0.4s]"></div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

              {/* Message input bar */}
              <form onSubmit={handleSendMessage} className="p-4 bg-white border-t border-gray-100 flex items-center space-x-2">
                <input 
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="พิมพ์คำถามเกี่ยวกับระเบียบการจดทะเบียน VAT เช่น เอกสารจดทะเบียน หรือ โทษการจดล่าช้า..."
                  className="flex-1 bg-gov-light/30 border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-gov-blue focus:bg-white text-gov-navy placeholder-gray-400 shadow-inner transition-all"
                  disabled={isLoading}
                />
                <button 
                  type="submit"
                  disabled={isLoading || !query.trim()}
                  className={`bg-gov-navy text-white p-3 rounded-xl hover:bg-gov-blue transition-all flex items-center justify-center ${
                    isLoading || !query.trim() ? "opacity-40 cursor-not-allowed" : "shadow-md shadow-gov-blue/10"
                  }`}
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>
            </section>

            {/* RIGHT VIEWPORT: REAL REAL-TIME TEXT INJECTION (LAWS & REGULATIONS) */}
            <section className="flex-1 bg-gov-light/45 flex flex-col md:w-2/5 overflow-hidden">
              
              <div className="px-6 py-4 border-b border-gray-200 bg-white flex items-center justify-between">
                <div className="flex items-center space-x-2 text-gov-navy">
                  <BookOpen className="w-4 h-4 text-gov-gold" />
                  <span className="text-xs md:text-sm font-bold tracking-wide uppercase">
                    ตัวบทกฎหมายและข้อบังคับดิบ (Real Text Injection)
                  </span>
                </div>
                <span className="bg-gov-gold/10 text-gov-navy text-[10px] font-bold px-2 py-0.5 rounded border border-gov-gold/25">
                  Vector Store Refs
                </span>
              </div>

              {/* Law Container */}
              {/* Inherits class computed by Accessibility dynamic scale state */}
              <div className={`flex-1 overflow-y-auto p-6 space-y-4 ${getLawFontSize()}`}>
                {injectedLaws.length > 0 ? (
                  injectedLaws.map((law, index) => (
                    <div 
                      key={law.id || index}
                      className="bg-white border border-gray-200/80 p-5 rounded-xl shadow-premium hover:shadow-md hover:border-gov-blue/30 transition-all duration-200 animate-fade-in"
                    >
                      {/* Document Code Header badge */}
                      <div className="flex items-center justify-between border-b border-gray-100 pb-2.5 mb-3">
                        <span className="text-gov-blue font-bold text-xs md:text-sm flex items-center space-x-1">
                          <FileText className="w-3.5 h-3.5 text-gov-gold flex-shrink-0" />
                          <span>{law.title}</span>
                        </span>
                        <span className="text-[10px] bg-gov-light text-gov-navy px-2 py-0.5 rounded font-mono">
                          ID: {law.id.toUpperCase()}
                        </span>
                      </div>
                      
                      {/* Raw document text body */}
                      <p className="text-gray-700 leading-relaxed font-serif bg-gray-50/50 p-3 rounded border border-gray-100 italic">
                        &ldquo;{law.content}&rdquo;
                      </p>
                    </div>
                  ))
                ) : (
                  <div className="h-full flex flex-col items-center justify-center text-center p-8 text-gray-400">
                    <div className="bg-white p-4 rounded-full shadow-premium mb-3 border border-gray-100 text-gov-gold">
                      <Scale className="w-8 h-8" />
                    </div>
                    <span className="text-sm font-semibold text-gov-navy mb-1">ยังไม่มีการค้นพบตัวบทกฎหมาย</span>
                    <span className="text-xs max-w-[280px]">
                      ส่งข้อความสืบค้นข้อมูลในช่องแชทซ้ายมือ เพื่อดึงข้อบังคับทางกฎหมายดิบที่เกี่ยวข้องเข้ามาแสดงตรงนี้แบบ Real-Time
                    </span>
                  </div>
                )}
              </div>

            </section>
          </div>
        )}

        {/* TAB 2: ADMIN ANALYTICS DASHBOARD */}
        {activeTab === "admin" && (
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            
            {/* Dashboard Title & Actions */}
            <div className="flex flex-wrap items-center justify-between border-b border-gray-200 pb-4">
              <div>
                <h2 className="text-lg md:text-xl font-bold text-gov-navy flex items-center space-x-2">
                  <BarChart3 className="w-5 h-5 text-gov-gold" />
                  <span>แผงควบคุมสถิติการสืบค้น (Admin Dashboard)</span>
                </h2>
                <p className="text-xs text-gray-500">
                  ติดตามคุณภาพการให้บริการ RAG, อัตราความถูกต้อง และสถิติการใช้งานคำถามในระบบ
                </p>
              </div>
              <div className="flex items-center space-x-2 mt-2 sm:mt-0">
                <button
                  onClick={fetchStats}
                  disabled={statsLoading}
                  className="bg-white border border-gray-200 hover:bg-gov-light text-gov-navy px-3.5 py-2 rounded-xl text-xs md:text-sm font-medium transition-all flex items-center space-x-1.5 shadow-sm"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${statsLoading ? "animate-spin" : ""}`} />
                  <span>รีเฟรชข้อมูล</span>
                </button>
                <button
                  onClick={handleResetDatabaseLogs}
                  className="bg-red-50 border border-red-100 hover:bg-red-100 text-red-700 px-3.5 py-2 rounded-xl text-xs md:text-sm font-medium transition-all flex items-center space-x-1.5 shadow-sm"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>รีเซ็ตประวัติทั้งหมด</span>
                </button>
              </div>
            </div>

            {statsLoading && !stats ? (
              <div className="h-64 flex items-center justify-center text-sm font-medium text-gov-navy">
                กำลังดาวน์โหลดข้อมูลการใช้งานสถิติ...
              </div>
            ) : (
              <>
                {/* 1. Counter Widgets Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  
                  {/* Card A: Total Sessions */}
                  <div className="bg-white border border-gray-200 p-5 rounded-xl shadow-premium flex items-center justify-between">
                    <div>
                      <span className="text-xs font-semibold text-gray-400 block mb-1">จำนวนผู้ใช้งาน (เซสชัน)</span>
                      <span className="text-2xl font-bold text-gov-navy">{stats?.total_sessions || 0}</span>
                    </div>
                    <div className="bg-gov-light p-3 rounded-lg text-gov-navy shadow-inner">
                      <Users className="w-5 h-5" />
                    </div>
                  </div>

                  {/* Card B: Total Interactions */}
                  <div className="bg-white border border-gray-200 p-5 rounded-xl shadow-premium flex items-center justify-between">
                    <div>
                      <span className="text-xs font-semibold text-gray-400 block mb-1">คำถามทั้งหมดสะสม</span>
                      <span className="text-2xl font-bold text-gov-navy">{stats?.total_interactions || 0}</span>
                    </div>
                    <div className="bg-gov-light p-3 rounded-lg text-gov-navy shadow-inner">
                      <MessageSquare className="w-5 h-5" />
                    </div>
                  </div>

                  {/* Card C: Out of Scope */}
                  <div className="bg-white border border-gray-200 p-5 rounded-xl shadow-premium flex items-center justify-between">
                    <div>
                      <span className="text-xs font-semibold text-gray-400 block mb-1">คำถามนอกขอบเขตระบบ</span>
                      <span className="text-2xl font-bold text-red-600">{stats?.total_out_of_scope || 0}</span>
                    </div>
                    <div className="bg-red-50 p-3 rounded-lg text-red-700 shadow-inner">
                      <AlertOctagon className="w-5 h-5" />
                    </div>
                  </div>

                  {/* Card D: Conflict Warning */}
                  <div className="bg-white border border-gray-200 p-5 rounded-xl shadow-premium flex items-center justify-between">
                    <div>
                      <span className="text-xs font-semibold text-gray-400 block mb-1">ตรวจพบข้อขัดแย้งของระเบียบ</span>
                      <span className="text-2xl font-bold text-amber-600">{stats?.total_conflicts || 0}</span>
                    </div>
                    <div className="bg-amber-50 p-3 rounded-lg text-amber-700 shadow-inner">
                      <AlertTriangle className="w-5 h-5" />
                    </div>
                  </div>

                </div>

                {/* 2. Top-5 Comparison Charts & Tables Column */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  
                  {/* Left Column: Top 5 In-Scope FAQs */}
                  <div className="bg-white border border-gray-200 p-5 rounded-xl shadow-premium flex flex-col">
                    <div className="border-b border-gray-100 pb-3 mb-4 flex items-center space-x-2">
                      <Compass className="w-4 h-4 text-gov-blue" />
                      <h3 className="text-sm md:text-base font-bold text-gov-navy">
                        5 อันดับคำถามที่พบบ่อย (In-Scope FAQs)
                      </h3>
                    </div>

                    {stats?.top_faq && stats.top_faq.length > 0 ? (
                      <div className="space-y-4 flex-1">
                        {stats.top_faq.map((item, idx) => {
                          // Find percentage relative to maximum interaction log counts
                          const maxCount = stats.top_faq[0]?.count || 1;
                          const pct = (item.count / maxCount) * 100;
                          return (
                            <div key={idx} className="space-y-1.5">
                              <div className="flex items-center justify-between text-xs md:text-sm font-medium">
                                <span className="text-gov-navy truncate max-w-[80%]" title={item.original_query}>
                                  {idx + 1}. {item.original_query}
                                </span>
                                <span className="text-gov-blue font-bold flex-shrink-0">{item.count} ครั้ง</span>
                              </div>
                              <div className="w-full bg-gray-100 rounded-full h-2">
                                <div 
                                  className="bg-gov-navy h-2 rounded-full transition-all duration-500" 
                                  style={{ width: `${pct}%` }}
                                ></div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="flex-1 flex items-center justify-center text-xs text-gray-400 py-12">
                        ไม่มีสถิติคำถามที่ตรงตามขอบเขตในขณะนี้
                      </div>
                    )}
                  </div>

                  {/* Right Column: Top 5 Out-of-Scope Logs */}
                  <div className="bg-white border border-gray-200 p-5 rounded-xl shadow-premium flex flex-col">
                    <div className="border-b border-gray-100 pb-3 mb-4 flex items-center space-x-2">
                      <AlertOctagon className="w-4 h-4 text-red-600" />
                      <h3 className="text-sm md:text-base font-bold text-gov-navy">
                        5 อันดับคำถามนอกขอบเขตการสืบค้น (Out-of-Scope Logs)
                      </h3>
                    </div>

                    {stats?.top_out_of_scope && stats.top_out_of_scope.length > 0 ? (
                      <div className="space-y-4 flex-1">
                        {stats.top_out_of_scope.map((item, idx) => {
                          const maxCount = stats.top_out_of_scope[0]?.count || 1;
                          const pct = (item.count / maxCount) * 100;
                          return (
                            <div key={idx} className="space-y-1.5">
                              <div className="flex items-center justify-between text-xs md:text-sm font-medium">
                                <span className="text-red-700 truncate max-w-[80%]" title={item.original_query}>
                                  🚨 {idx + 1}. {item.original_query}
                                </span>
                                <span className="text-red-600 font-bold flex-shrink-0">{item.count} ครั้ง</span>
                              </div>
                              <div className="w-full bg-gray-100 rounded-full h-2">
                                <div 
                                  className="bg-red-500 h-2 rounded-full transition-all duration-500" 
                                  style={{ width: `${pct}%` }}
                                ></div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="flex-1 flex items-center justify-center text-xs text-gray-400 py-12">
                        ไม่มีสถิติคำถามนอกขอบเขตในขณะนี้
                      </div>
                    )}
                  </div>
                </div>

                {/* 3. Recent Chat Interactions Logbook */}
                <div className="bg-white border border-gray-200 p-5 rounded-xl shadow-premium flex flex-col space-y-4">
                  <div className="border-b border-gray-100 pb-3 flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-gov-blue" />
                    <h3 className="text-sm md:text-base font-bold text-gov-navy">
                      บันทึกประวัติการสืบค้นล่าสุดของระบบ (Recent Chat Logs - API: /api/logs)
                    </h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs md:text-sm border-collapse">
                      <thead>
                        <tr className="bg-gov-light/50 border-b border-gray-200 text-gov-navy font-bold">
                          <th className="p-3">เวลา (Timestamp)</th>
                          <th className="p-3">Session ID</th>
                          <th className="p-3">คำถามผู้ใช้ (Original Query)</th>
                          <th className="p-3">คำถามที่เกลาใหม่ (Rewritten)</th>
                          <th className="p-3 text-center">ขอบเขต (Scope)</th>
                          <th className="p-3 text-center">ข้อขัดแย้ง?</th>
                        </tr>
                      </thead>
                      <tbody>
                        {recentLogs.length > 0 ? (
                          recentLogs.map((log) => (
                            <tr key={log.id} className="border-b border-gray-100 hover:bg-gov-light/35 transition-colors">
                              <td className="p-3 text-gray-500 whitespace-nowrap">
                                {new Date(log.timestamp).toLocaleString("th-TH")}
                              </td>
                              <td className="p-3 font-mono text-gov-blue text-[11px]">{log.session_id}</td>
                              <td className="p-3 text-gov-navy max-w-[200px] truncate" title={log.original_query}>
                                {log.original_query}
                              </td>
                              <td className="p-3 text-gray-500 max-w-[200px] truncate" title={log.rewritten_query}>
                                {log.rewritten_query || "-"}
                              </td>
                              <td className="p-3 text-center">
                                {log.is_out_of_scope === 1 ? (
                                  <span className="bg-red-50 text-red-700 border border-red-100 text-[10px] font-bold px-2 py-0.5 rounded-full">
                                    Out-of-Scope
                                  </span>
                                ) : (
                                  <span className="bg-green-50 text-green-700 border border-green-100 text-[10px] font-bold px-2 py-0.5 rounded-full">
                                    In-Scope
                                  </span>
                                )}
                              </td>
                              <td className="p-3 text-center">
                                {log.detected_conflict === 1 ? (
                                  <span className="bg-amber-50 text-amber-700 border border-amber-100 text-[10px] font-bold px-2 py-0.5 rounded-full">
                                    พบข้อขัดแย้ง
                                  </span>
                                ) : (
                                  <span className="text-gray-400">-</span>
                                )}
                              </td>
                            </tr>
                          ))
                        ) : (
                          <tr>
                            <td colSpan={6} className="p-6 text-center text-gray-400">ยังไม่มีข้อมูลบันทึกในระบบ</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* 4. Vector Knowledge Base Explorer */}
                <div className="bg-white border border-gray-200 p-5 rounded-xl shadow-premium flex flex-col space-y-4">
                  <div className="border-b border-gray-100 pb-3 flex items-center space-x-2">
                    <Scale className="w-4 h-4 text-gov-gold" />
                    <h3 className="text-sm md:text-base font-bold text-gov-navy">
                      คลังเอกสารกฎระเบียบเวกเตอร์ดัชนี (Vector Store Index Explorer - API: /api/laws)
                    </h3>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {lawsList.length > 0 ? (
                      lawsList.map((law, idx) => (
                        <div key={law.id || idx} className="bg-gov-light/35 border border-gray-200 p-4 rounded-xl space-y-3">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-gov-navy text-xs md:text-sm">{law.title}</span>
                            <span className="bg-gov-navy text-white text-[10px] font-mono px-2 py-0.5 rounded uppercase">
                              {law.id}
                            </span>
                          </div>
                          <p className="text-xs text-gray-600 leading-relaxed italic bg-white p-3 rounded border border-gray-100">
                            &ldquo;{law.content}&rdquo;
                          </p>
                          <div className="flex flex-wrap gap-1.5 pt-1">
                            {law.keywords.map((kw: string, kIdx: number) => (
                              <span key={kIdx} className="bg-gov-gold/10 text-gov-navy border border-gov-gold/25 text-[10px] px-2 py-0.5 rounded-full font-medium">
                                #{kw}
                              </span>
                            ))}
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="col-span-2 py-12 text-center text-gray-400 text-xs">
                        ไม่มีข้อมูลดัชนีเอกสารในคลังเวกเตอร์
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}

          </div>
        )}

      </main>

      {/* --- FOOTER LICENSE --- */}
      <footer className="bg-white border-t border-gray-100 px-6 py-3 text-center text-[10px] md:text-xs text-gray-400 flex flex-col sm:flex-row items-center justify-between shrink-0">
        <span>© 2026 กรมสรรพากร กระทรวงการคลัง. ระบบปิดความมั่นคงสูง (Local RAG Deployment).</span>
        <span className="mt-1 sm:mt-0 font-medium">การศึกษาอิสระ (IS) คณะสถิติประยุกต์ สถาบันบัณฑิตพัฒนบริหารศาสตร์ (NIDA)</span>
      </footer>

    </div>
  );
}
