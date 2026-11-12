"use client"

import { ArrowLeft, ChevronRight, CheckCircle2, Check, Sparkles } from 'lucide-react'
import { useParams, useRouter } from 'next/navigation'
import { MANUFACTURING_STEPS } from '../../../../common/initail'

const Order = () => {
    const { id: orderId } = useParams()
    const router = useRouter()

    // mockup
    const selectedOrder = {
    id: 'ORD-2026-001',
    itemName: 'Pastel Linen Summer Dress',
    customer: 'คุณแพรวา (Mellow Studio)',
    quantity: 120,
    currentStep: 4,
    status: 'in_progress', // 'in_progress' | 'completed' | 'failed'
    dueDate: '20 พ.ย. 2026',
    resources: {
      machineHours: '32 / 48 ชม.',
      fabricUsed: '185 เมตร',
      laborCount: '6 คน',
    },
    logs: [
      { step: 1, note: 'อนุมัติไฟล์ CAD และตัดแพทเทิร์นเรียบร้อย', time: '10 พ.ย. 09:30' },
      { step: 2, note: 'ตรวจรับผ้าลินินสีชมพูพาสเทล ผ่านเกณฑ์ทนความร้อน', time: '11 พ.ย. 14:15' },
      { step: 3, note: 'ย้อมสีและอบแห้งครบตาม Dye lot', time: '12 พ.ย. 11:00' },
    ]
  }

  {/* =========================================================
            หน้า 2: ORDER DETAILS (รายละเอียดและไทม์ไลน์ 6 ขั้นตอน)
           ========================================================= */}
    return <div className="space-y-6 animate-fadeIn">
            {/* Back Button */}
            <button 
              onClick={() => {router.push('/')}}
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
                      {orderId}
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
                  <div
                    className="px-6 py-3 bg-gradient-to-r from-pink-400 to-purple-400 hover:from-pink-500 hover:to-purple-500 text-white text-sm font-semibold rounded-2xl shadow-md shadow-pink-200/60 flex items-center justify-center gap-2 transition-all duration-300 hover:scale-[1.02] active:scale-95"
                  >
                    <span>{selectedOrder.currentStep === 6 ? 'ยืนยันจัดส่งสำเร็จ' : `เสร็จสิ้น Step ${selectedOrder.currentStep} → ขั้นถัดไป`}</span>
                    <ChevronRight className="w-4 h-4" />
                  </div>
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
}

export default Order