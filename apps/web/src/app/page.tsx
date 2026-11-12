"use client"

import React, { useState } from 'react';
import { 
  Scissors, Layers, Sparkles, Shirt, CheckCircle2, Truck, 
  AlertCircle, ArrowLeft, Plus, Clock, Package, RotateCcw, 
  ChevronRight, Search, Check
} from 'lucide-react';
import { INITIAL_ORDERS } from '../../common/initail';

// ข้อมูลจำลองทั้ง 6 ขั้นตอนการผลิตเสื้อผ้า
const MANUFACTURING_STEPS = [
  { id: 1, name: 'Design & Pattern', thName: 'ออกแบบและตัดแพทเทิร์น', icon: Scissors, color: 'bg-pink-100 text-pink-600' },
  { id: 2, name: 'Fabric Sourcing', thName: 'จัดหาและวัดขนาดผ้า', icon: Layers, color: 'bg-purple-100 text-purple-600' },
  { id: 3, name: 'Fabric Finishing', thName: 'ย้อมสีและตกแต่งผ้า', icon: Sparkles, color: 'bg-indigo-100 text-indigo-600' },
  { id: 4, name: 'Garment Assembly', thName: 'ตัดเย็บและประกอบชุด', icon: Shirt, color: 'bg-sky-100 text-sky-600' },
  { id: 5, name: 'Quality Assurance', thName: 'ตรวจสอบคุณภาพ (QA)', icon: CheckCircle2, color: 'bg-teal-100 text-teal-600' },
  { id: 6, name: 'Packaging & Delivery', thName: 'แพ็คสินค้าและจัดส่ง', icon: Truck, color: 'bg-emerald-100 text-emerald-600' },
];

export default function GarmentTrackerApp() {
  const [orders, setOrders] = useState(INITIAL_ORDERS);
  // 'list' | 'details' | 'failed'
  const [activeTab, setActiveTab] = useState('list'); 
  const [selectedOrderId, setSelectedOrderId] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);

  // State สำหรับสร้าง Order ใหม่
  const [newOrder, setNewOrder] = useState({ itemName: '', customer: '', quantity: 50, dueDate: '30 พ.ย. 2026' });

  const selectedOrder = orders.find(o => o.id === selectedOrderId);
  const activeOrders = orders.filter(o => o.status !== 'failed' && 
    (o.itemName.toLowerCase().includes(searchQuery.toLowerCase()) || o.id.toLowerCase().includes(searchQuery.toLowerCase()))
  );
  const failedOrders = orders.filter(o => o.status === 'failed');

  // ฟังก์ชันกดเลื่อน Step การผลิตในหน้า Details
  const handleAdvanceStep = (orderId: string) => {
    setOrders(prev => prev.map(order => {
      if (order.id !== orderId) return order;
      if (order.currentStep < 6) {
        const nextStep = order.currentStep + 1;
        const stepInfo = MANUFACTURING_STEPS.find(s => s.id === nextStep);
        return {
          ...order,
          currentStep: nextStep,
          logs: [
            ...order.logs,
            { step: nextStep, note: `เริ่มดำเนินการขั้นตอน: ${stepInfo?.thName}`, time: 'เมื่อสักครู่' }
          ]
        };
      } else {
        return {
          ...order,
          status: 'completed',
          logs: [
            ...order.logs,
            { step: 6, note: 'จัดส่งสำเร็จครบถ้วน!', time: 'เมื่อสักครู่' }
          ]
        };
      }
    }));
  };

  // ฟังก์ชันกู้คืน Order ที่จัดส่งไม่สำเร็จกลับเข้าสู่ระบบ
  const handleRetryOrder = (orderId: string) => {
    setOrders(prev => prev.map(order => {
      if (order.id !== orderId) return order;
      return {
        ...order,
        status: 'in_progress',
        logs: [
          ...order.logs,
          { step: order.currentStep, note: 'นำออเดอร์กลับเข้าสู่กระบวนการแก้ไขและจัดส่งใหม่', time: 'เมื่อสักครู่' }
        ]
      };
    }));
    setActiveTab('list');
  };

  // ฟังก์ชันเพิ่ม Order ใหม่
  const handleCreateOrder = (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!newOrder.itemName || !newOrder.customer) return;
    const created = {
      id: `ORD-2026-00${orders.length + 1}`,
      itemName: newOrder.itemName,
      customer: newOrder.customer,
      quantity: Number(newOrder.quantity),
      currentStep: 1,
      status: 'in_progress',
      dueDate: newOrder.dueDate,
      resources: { machineHours: '0 / 24 ชม.', fabricUsed: '0 เมตร', laborCount: '2 คน' },
      logs: [{ step: 1, note: 'เปิดออเดอร์ใหม่ รอ Designer สร้างไฟล์ CAD', time: 'เมื่อสักครู่' }]
    };
    setOrders([created, ...orders]);
    setNewOrder({ itemName: '', customer: '', quantity: 50, dueDate: '30 พ.ย. 2026' });
    setIsModalOpen(false);
  };

  return (
    <div className="min-h-screen bg-[#FDFBF7] text-slate-700 font-sans selection:bg-pink-200">
      {/* Custom Keyframes สำหรับ Shimmer บน Progress Bar */}
      <style>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        .animate-shimmer {
          animation: shimmer 2s infinite linear;
        }
      `}</style>

      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-md border-b border-pink-100/80 px-6 py-4">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          {/* Brand Logo */}
          <div 
            onClick={() => { setActiveTab('list'); setSelectedOrderId(""); }}
            className="flex items-center gap-3 cursor-pointer group"
          >
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-pink-200 to-purple-200 flex items-center justify-center shadow-sm group-hover:rotate-6 transition-transform duration-300">
              <Shirt className="w-5 h-5 text-pink-600" />
            </div>
            <div>
              <h1 className="text-lg font-bold bg-gradient-to-r from-pink-500 to-purple-500 bg-clip-text text-transparent">
                StitchFlow Studio
              </h1>
              <p className="text-xs text-slate-400">ระบบติดตามการผลิตเสื้อผ้า 6 ขั้นตอน</p>
            </div>
          </div>

          {/* Navigation Pills */}
          <nav className="flex items-center bg-slate-100/80 p-1.5 rounded-2xl border border-slate-200/50">
            <button
              onClick={() => { setActiveTab('list'); setSelectedOrderId(""); }}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300 flex items-center gap-2 ${
                activeTab === 'list' || activeTab === 'details'
                  ? 'bg-white text-pink-600 shadow-sm scale-100' 
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <Package className="w-4 h-4" />
              รายการผลิต ({activeOrders.length})
            </button>

            <button
              onClick={() => { setActiveTab('failed'); setSelectedOrderId(''); }}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300 flex items-center gap-2 ${
                activeTab === 'failed'
                  ? 'bg-rose-50 text-rose-600 shadow-sm ring-1 ring-rose-200' 
                  : 'text-slate-500 hover:text-rose-500'
              }`}
            >
              <AlertCircle className="w-4 h-4" />
              จัดส่งไม่สำเร็จ
              {failedOrders.length > 0 && (
                <span className="px-2 py-0.5 text-xs bg-rose-200 text-rose-700 rounded-full animate-pulse">
                  {failedOrders.length}
                </span>
              )}
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-5xl mx-auto px-6 py-8">
        
        {/* =========================================================
            หน้า 1: ORDER LIST (รายการคำสั่งผลิตทั้งหมด)
           ========================================================= */}
        {activeTab === 'list' && (
          <div className="space-y-6 animate-fadeIn">
            {/* Header & Search & Add Button */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div>
                <h2 className="text-2xl font-bold text-slate-800">รายการสั่งตัดเสื้อผ้า ✨</h2>
                <p className="text-sm text-slate-400 mt-0.5">ติดตามสถานะและทรัพยากรการผลิตแบบเรียลไทม์</p>
              </div>

              <div className="flex items-center gap-3 w-full sm:w-auto">
                <div className="relative flex-1 sm:w-60">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input 
                    type="text" 
                    placeholder="ค้นหารหัสหรือชื่อชุด..." 
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 bg-white border border-pink-100 rounded-2xl text-sm focus:outline-none focus:ring-2 focus:ring-pink-200 transition-all"
                  />
                </div>

                <button 
                  onClick={() => setIsModalOpen(true)}
                  className="px-4 py-2.5 bg-gradient-to-r from-pink-400 to-purple-400 hover:from-pink-500 hover:to-purple-500 text-white text-sm font-medium rounded-2xl shadow-sm shadow-pink-200 flex items-center gap-2 transition-all duration-300 hover:-translate-y-0.5 active:scale-95 shrink-0"
                >
                  <Plus className="w-4 h-4" />
                  สร้างออเดอร์
                </button>
              </div>
            </div>

            {/* Order Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {activeOrders.map((order) => {
                const progressPercent = order.status === 'completed' 
                  ? 100 
                  : Math.round(((order.currentStep - 0.5) / 6) * 100);
                const currentStepObj = MANUFACTURING_STEPS.find(s => s.id === order.currentStep);
                const StepIcon = currentStepObj?.icon || Shirt;

                return (
                  <div 
                    key={order.id}
                    onClick={() => { setSelectedOrderId(order.id); setActiveTab('details'); }}
                    className="group bg-white rounded-3xl p-6 border border-pink-100/80 shadow-sm hover:shadow-md hover:shadow-pink-100/50 hover:-translate-y-1 transition-all duration-300 cursor-pointer relative overflow-hidden"
                  >
                    {/* Top Row: ID & Status Badge */}
                    <div className="flex justify-between items-start mb-3">
                      <span className="text-xs font-semibold tracking-wider text-purple-500 bg-purple-50 px-3 py-1 rounded-full">
                        {order.id}
                      </span>
                      {order.status === 'completed' ? (
                        <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-3 py-1 rounded-full flex items-center gap-1">
                          <Check className="w-3.5 h-3.5" /> เสร็จสมบูรณ์
                        </span>
                      ) : (
                        <span className="text-xs font-medium text-amber-600 bg-amber-50 px-3 py-1 rounded-full flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
                          กำลังผลิต (Step {order.currentStep}/6)
                        </span>
                      )}
                    </div>

                    {/* Title & Customer */}
                    <h3 className="text-lg font-bold text-slate-800 group-hover:text-pink-600 transition-colors">
                      {order.itemName}
                    </h3>
                    <p className="text-sm text-slate-400 mb-5">
                      ลูกค้า: {order.customer} • จำนวน <span className="text-slate-600 font-medium">{order.quantity} ตัว</span>
                    </p>

                    {/* Current Step Pill */}
                    <div className="flex items-center gap-2.5 bg-slate-50/80 p-3 rounded-2xl mb-4 border border-slate-100">
                      <div className={`w-8 h-8 rounded-xl flex items-center justify-center ${currentStepObj?.color}`}>
                        <StepIcon className="w-4 h-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-[11px] text-slate-400">ขั้นตอนปัจจุบัน</p>
                        <p className="text-xs font-semibold text-slate-700 truncate">
                          {order.status === 'completed' ? 'จัดส่งถึงลูกค้าเรียบร้อย' : currentStepObj?.thName}
                        </p>
                      </div>
                      <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-pink-400 group-hover:translate-x-1 transition-all" />
                    </div>

                    {/* Animated Progress Bar */}
                    <div>
                      <div className="flex justify-between text-xs mb-1.5">
                        <span className="text-slate-400 flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5" /> กำหนดส่ง: {order.dueDate}
                        </span>
                        <span className="font-bold text-pink-500">{progressPercent}%</span>
                      </div>
                      <div className="w-full h-2.5 bg-pink-50 rounded-full overflow-hidden p-0.5">
                        <div 
                          className="h-full rounded-full bg-gradient-to-r from-pink-300 via-purple-300 to-indigo-300 transition-all duration-700 ease-out relative overflow-hidden"
                          style={{ width: `${progressPercent}%` }}
                        >
                          {/* Shimmer Light Effect */}
                          <div className="absolute inset-0 bg-white/40 animate-shimmer" />
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* =========================================================
            หน้า 2: ORDER DETAILS (รายละเอียดและไทม์ไลน์ 6 ขั้นตอน)
           ========================================================= */}
        {activeTab === 'details' && selectedOrder && (
          <div className="space-y-6 animate-fadeIn">
            {/* Back Button */}
            <button 
              onClick={() => setActiveTab('list')}
              className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-pink-600 bg-white px-4 py-2 rounded-2xl border border-slate-100 shadow-sm transition-all hover:-translate-x-1"
            >
              <ArrowLeft className="w-4 h-4" />
              กลับหน้ารายการ
            </button>

            {/* Main Detail Card */}
            <div className="bg-white rounded-3xl p-6 sm:p-8 border border-pink-100 shadow-sm">
              <div className="flex flex-col md:flex-row justify-between md:items-center gap-4 pb-6 border-b border-slate-100">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-xs font-bold text-purple-600 bg-purple-50 px-3 py-1 rounded-full">
                      {selectedOrder.id}
                    </span>
                    <span className="text-xs text-slate-400">กำหนดส่ง: {selectedOrder.dueDate}</span>
                  </div>
                  <h2 className="text-2xl font-bold text-slate-800">{selectedOrder.itemName}</h2>
                  <p className="text-sm text-slate-500 mt-1">
                    ลูกค้า: <span className="font-medium text-slate-700">{selectedOrder.customer}</span> • จำนวนสั่งผลิต <span className="font-medium text-slate-700">{selectedOrder.quantity} ตัว</span>
                  </p>
                </div>

                {/* Action Button: เลื่อนขั้นต่อไป */}
                {selectedOrder.status !== 'completed' ? (
                  <button
                    onClick={() => handleAdvanceStep(selectedOrder.id)}
                    className="px-6 py-3 bg-gradient-to-r from-pink-400 to-purple-400 hover:from-pink-500 hover:to-purple-500 text-white text-sm font-semibold rounded-2xl shadow-md shadow-pink-200/60 flex items-center justify-center gap-2 transition-all duration-300 hover:scale-[1.02] active:scale-95"
                  >
                    <span>{selectedOrder.currentStep === 6 ? 'ยืนยันจัดส่งสำเร็จ' : `เสร็จสิ้น Step ${selectedOrder.currentStep} → ขั้นถัดไป`}</span>
                    <ChevronRight className="w-4 h-4" />
                  </button>
                ) : (
                  <div className="px-5 py-2.5 bg-emerald-50 text-emerald-600 border border-emerald-200 rounded-2xl text-sm font-semibold flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5" />
                    ปิดงานเรียบร้อยแล้ว
                  </div>
                )}
              </div>

              {/* 6-Step Visual Stepper */}
              <div className="py-8">
                <h3 className="text-sm font-bold text-slate-700 mb-6">ความคืบหน้ากระบวนการผลิต (6 ขั้นตอน)</h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
                  {MANUFACTURING_STEPS.map((step) => {
                    const Icon = step.icon;
                    const isCompleted = selectedOrder.status === 'completed' || step.id < selectedOrder.currentStep;
                    const isCurrent = selectedOrder.status !== 'completed' && step.id === selectedOrder.currentStep;

                    return (
                      <div 
                        key={step.id}
                        className={`relative p-4 rounded-2xl border transition-all duration-500 flex flex-col items-center text-center ${
                          isCompleted 
                            ? 'bg-emerald-50/40 border-emerald-200/80' 
                            : isCurrent 
                              ? 'bg-pink-50/60 border-pink-300 shadow-sm scale-105' 
                              : 'bg-slate-50/50 border-slate-100 opacity-60'
                        }`}
                      >
                        <div className={`w-11 h-11 rounded-2xl flex items-center justify-center mb-3 transition-transform duration-300 ${
                          isCompleted ? 'bg-emerald-100 text-emerald-600' : isCurrent ? `${step.color} animate-bounce` : 'bg-slate-200/70 text-slate-400'
                        }`}>
                          {isCompleted ? <Check className="w-5 h-5" /> : <Icon className="w-5 h-5" />}
                        </div>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-0.5">
                          Step {step.id}
                        </span>
                        <p className={`text-xs font-semibold ${isCurrent ? 'text-pink-600' : 'text-slate-700'}`}>
                          {step.thName}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Resource Consumption & Activity Logs */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4 border-t border-slate-100">
                {/* Resource Box */}
                <div className="bg-[#FDFBF7] p-5 rounded-2xl border border-amber-100/80 space-y-3">
                  <h4 className="text-sm font-bold text-slate-700 flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-amber-500" />
                    ทรัพยากรที่ใช้ไป (Resources)
                  </h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between py-1.5 border-b border-amber-100/50">
                      <span className="text-slate-500">เวลาเครื่องจักร:</span>
                      <span className="font-semibold text-slate-700">{selectedOrder.resources.machineHours}</span>
                    </div>
                    <div className="flex justify-between py-1.5 border-b border-amber-100/50">
                      <span className="text-slate-500">ปริมาณผ้าที่ใช้:</span>
                      <span className="font-semibold text-slate-700">{selectedOrder.resources.fabricUsed}</span>
                    </div>
                    <div className="flex justify-between py-1.5">
                      <span className="text-slate-500">ทีมช่างปฏิบัติงาน:</span>
                      <span className="font-semibold text-slate-700">{selectedOrder.resources.laborCount}</span>
                    </div>
                  </div>
                </div>

                {/* Tracking Logs */}
                <div className="md:col-span-2 bg-slate-50/70 p-5 rounded-2xl border border-slate-100">
                  <h4 className="text-sm font-bold text-slate-700 mb-4">บันทึกการติดตามงาน (Tracking History)</h4>
                  <div className="space-y-3">
                    {selectedOrder.logs.map((log, idx) => (
                      <div key={idx} className="flex items-start gap-3 bg-white p-3 rounded-xl border border-slate-100 shadow-2xs">
                        <span className="px-2 py-0.5 text-[11px] font-bold bg-purple-100 text-purple-600 rounded-lg shrink-0 mt-0.5">
                          Step {log.step}
                        </span>
                        <div className="flex-1">
                          <p className="text-xs font-medium text-slate-700">{log.note}</p>
                          <p className="text-[11px] text-slate-400 mt-0.5">{log.time}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* =========================================================
            หน้า 3: FAILED DELIVERIES (รายการออเดอร์ที่จัดส่งไม่สำเร็จ)
           ========================================================= */}
        {activeTab === 'failed' && (
          <div className="space-y-6 animate-fadeIn">
            <div>
              <h2 className="text-2xl font-bold text-rose-600 flex items-center gap-2">
                ออเดอร์ที่จัดส่งไม่สำเร็จ / ตีกลับ 🧸
              </h2>
              <p className="text-sm text-slate-400 mt-0.5">
                รายการที่เกิดปัญหาในขั้นตอน QA หรือการขนส่ง สามารถตรวจสอบสาเหตุและนำกลับเข้าไลน์ผลิตใหม่ได้
              </p>
            </div>

            {failedOrders.length === 0 ? (
              <div className="bg-white rounded-3xl p-12 text-center border border-pink-100">
                <div className="w-16 h-16 bg-emerald-50 text-emerald-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle2 className="w-8 h-8" />
                </div>
                <h3 className="text-lg font-bold text-slate-700">ยอดเยี่ยม! ไม่มีออเดอร์ที่จัดส่งไม่สำเร็จ</h3>
                <p className="text-sm text-slate-400 mt-1">ทุกคำสั่งซื้อกำลังดำเนินการและจัดส่งได้อย่างราบรื่น</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {failedOrders.map((order) => (
                  <div 
                    key={order.id}
                    className="bg-white rounded-3xl p-6 border-2 border-rose-100 shadow-sm hover:shadow-md transition-all duration-300 flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex justify-between items-center mb-3">
                        <span className="text-xs font-bold text-rose-600 bg-rose-50 px-3 py-1 rounded-full">
                          {order.id}
                        </span>
                        <span className="text-xs text-slate-400">
                          วันที่ตีกลับ: {order.failedDate}
                        </span>
                      </div>

                      <h3 className="text-lg font-bold text-slate-800">{order.itemName}</h3>
                      <p className="text-sm text-slate-500 mb-4">
                        ลูกค้า: {order.customer} • จำนวน {order.quantity} ตัว
                      </p>

                      {/* กล่องแสดงสาเหตุที่จัดส่งไม่สำเร็จ */}
                      <div className="bg-rose-50/70 border border-rose-200/70 rounded-2xl p-4 mb-5">
                        <p className="text-xs font-bold text-rose-600 flex items-center gap-1.5 mb-1">
                          <AlertCircle className="w-4 h-4" />
                          สาเหตุที่ไม่สำเร็จ (ติดอยู่ที่ Step {order.currentStep}):
                        </p>
                        <p className="text-xs text-rose-800 leading-relaxed">
                          {order.failReason}
                        </p>
                      </div>
                    </div>

                    {/* ปุ่ม Action นำกลับไปแก้ไข */}
                    <div className="flex items-center gap-3 pt-2">
                      <button
                        onClick={() => handleRetryOrder(order.id)}
                        className="flex-1 py-2.5 px-4 bg-rose-500 hover:bg-rose-600 text-white text-xs font-semibold rounded-2xl shadow-sm shadow-rose-200 flex items-center justify-center gap-2 transition-all duration-300 hover:-translate-y-0.5 active:scale-95"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                        นำกลับเข้าไลน์แก้ไข / จัดส่งใหม่
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      {/* Modal สร้าง Order ใหม่ */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/20 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 border border-pink-100 shadow-xl animate-fadeIn">
            <h3 className="text-lg font-bold text-slate-800 mb-1">สร้างคำสั่งผลิตเสื้อผ้าใหม่ 🎀</h3>
            <p className="text-xs text-slate-400 mb-5">ออเดอร์ใหม่จะเริ่มต้นที่ Step 1 (ออกแบบและตัดแพทเทิร์น)</p>
            
            <form onSubmit={handleCreateOrder} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">ชื่อรุ่นเสื้อผ้า / สินค้า</label>
                <input 
                  type="text" 
                  required
                  placeholder="เช่น Pastel Cotton Shirt"
                  value={newOrder.itemName}
                  onChange={e => setNewOrder({...newOrder, itemName: e.target.value})}
                  className="w-full px-4 py-2.5 rounded-2xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-pink-200"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">ชื่อลูกค้า / แบรนด์</label>
                <input 
                  type="text" 
                  required
                  placeholder="เช่น คุณมิลิน (Soft Studio)"
                  value={newOrder.customer}
                  onChange={e => setNewOrder({...newOrder, customer: e.target.value})}
                  className="w-full px-4 py-2.5 rounded-2xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-pink-200"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">จำนวน (ตัว)</label>
                  <input 
                    type="number" 
                    min="1"
                    value={newOrder.quantity}
                    onChange={e => setNewOrder({...newOrder, quantity: parseInt(e.target.value)})}
                    className="w-full px-4 py-2.5 rounded-2xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-pink-200"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">กำหนดส่ง</label>
                  <input 
                    type="text" 
                    value={newOrder.dueDate}
                    onChange={e => setNewOrder({...newOrder, dueDate: e.target.value})}
                    className="w-full px-4 py-2.5 rounded-2xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-pink-200"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <button 
                  type="button" 
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-500 hover:bg-slate-100 rounded-xl transition-colors"
                >
                  ยกเลิก
                </button>
                <button 
                  type="submit"
                  className="px-5 py-2.5 bg-gradient-to-r from-pink-400 to-purple-400 text-white text-xs font-semibold rounded-xl shadow-sm hover:opacity-95 transition-all active:scale-95"
                >
                  เพิ่มเข้าระบบ
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}