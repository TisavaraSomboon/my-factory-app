"use client"

import { 
   CheckCircle2,AlertCircle, RotateCcw
} from 'lucide-react';
import { Order } from '../../../type/order.type';

const HodingOrder = () => {
    // const failedOrders = orders.filter(o => o.status === 'failed');
    const failedOrders: any = []
    // ฟังก์ชันกู้คืน Order ที่จัดส่งไม่สำเร็จกลับเข้าสู่ระบบ
  const handleRetryOrder = (orderId: string) => {
    // setOrders(prev => prev.map(order => {
    //   if (order.id !== orderId) return order;
    //   return {
    //     ...order,
    //     status: 'in_progress',
    //     logs: [
    //       ...order.logs,
    //       { step: order.currentStep, note: 'นำออเดอร์กลับเข้าสู่กระบวนการแก้ไขและจัดส่งใหม่', time: 'เมื่อสักครู่' }
    //     ]
    //   };
    // }));
    // setActiveTab('list');
  };
{/* =========================================================
            หน้า 3: FAILED DELIVERIES (รายการออเดอร์ที่จัดส่งไม่สำเร็จ)
           ========================================================= */}
    return <div className="space-y-6 animate-fadeIn">
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
                {failedOrders.map((order: Order) => (
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
}

export default HodingOrder