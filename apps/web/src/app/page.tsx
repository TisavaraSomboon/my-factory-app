"use client"

import React, { useState } from 'react';
import { 
  Shirt, CheckCircle2, 
  AlertCircle, Plus, Clock, RotateCcw, 
  ChevronRight, Search, Check
} from 'lucide-react';
import { INITIAL_ORDERS, MANUFACTURING_STEPS } from '../../common/initail';
import { useRouter } from 'next/navigation';
import CreateOrderModal from '@/component/CreateOrderModal';

export default function GarmentTrackerApp() {
  const [orders, setOrders] = useState(INITIAL_ORDERS);
  // 'list' | 'details' | 'failed'
  const [activeTab, setActiveTab] = useState('list'); 
  const [searchQuery, setSearchQuery] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);

  // State สำหรับสร้าง Order ใหม่
  const activeOrders = orders.filter(o => o.status !== 'failed' && 
    (o.itemName.toLowerCase().includes(searchQuery.toLowerCase()) || o.id.toLowerCase().includes(searchQuery.toLowerCase()))
  );
  const failedOrders = orders.filter(o => o.status === 'failed');
  const router = useRouter()

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

  return (
    <div>
      {/* Main Content Area */}
      <main>
        
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
                    onClick={() => { router.push(`order/${order.id}`) }}
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
      {isModalOpen && <CreateOrderModal laseOrderID={orders[orders.length-1].id} handleCloseModal={() => { setIsModalOpen(false)}} />}
    </div>
  );
}