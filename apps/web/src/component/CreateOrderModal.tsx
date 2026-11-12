import { useForm } from 'react-hook-form';
import { X, Sparkles} from 'lucide-react'

type Props = {
    laseOrderID: string
    handleCloseModal: () => void
}

type NewOrder = {
    itemName: string,
      customer: string,
      quantity: number,
      dueDate: string
}

const CreateOrderModal = ({ laseOrderID, handleCloseModal }: Props) => {
    const { 
    register, 
    handleSubmit, 
    formState: { errors } 
  } = useForm<NewOrder>({
    defaultValues: {
      itemName: '',
      customer: '',
      quantity: 50,
      dueDate: '30 พ.ย. 2026'
    }
  });
  
    // ฟังก์ชันเพิ่ม Order ใหม่
  const onFormSubmit = (data: NewOrder) => {
    const created = {
      id: `ORD-2026-00${parseInt(laseOrderID[laseOrderID.length - 1]) + 1}`,
      itemName: data.itemName,
      customer: data.customer,
      quantity: Number(data.quantity),
      currentStep: 1,
      status: 'in_progress',
      dueDate: data.dueDate,
      resources: { machineHours: '0 / 24 ชม.', fabricUsed: '0 เมตร', laborCount: '2 คน' },
      logs: [{ step: 1, note: 'เปิดออเดอร์ใหม่ รอ Designer สร้างไฟล์ CAD', time: 'เมื่อสักครู่' }]
    };
    // onSubmit([created, ...orders]);
    handleCloseModal();
  };

    return <div className="fixed inset-0 z-50 bg-slate-900/20 backdrop-blur-xs flex items-center justify-center p-4 animate-fadeIn">
      <div className="bg-white rounded-3xl max-w-md w-full p-6 border border-pink-100 shadow-xl relative">
        
        {/* Close Button */}
        <button 
          onClick={handleCloseModal}
          className="absolute top-5 right-5 text-slate-400 hover:text-slate-600 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 mb-1">
          <Sparkles className="w-5 h-5 text-pink-500" />
          <h3 className="text-lg font-bold text-slate-800">สร้างคำสั่งผลิตเสื้อผ้าใหม่</h3>
        </div>
        <p className="text-xs text-slate-400 mb-5">ออเดอร์ใหม่จะเริ่มต้นที่ Step 1 (ออกแบบและตัดแพทเทิร์น)</p>
        
        {/* ฟอร์มที่ผูกกับ react-hook-form */}
        <form onSubmit={() => handleSubmit(onFormSubmit)} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">ชื่อรุ่นเสื้อผ้า / สินค้า</label>
            <input 
              type="text" 
              placeholder="เช่น Pastel Cotton Shirt"
              {...register("itemName", { required: "กรุณากรอกชื่อสินค้า" })}
              className={`w-full px-4 py-2.5 rounded-2xl border text-sm focus:outline-none focus:ring-2 transition-all ${
                errors.itemName ? 'border-rose-300 focus:ring-rose-200' : 'border-slate-200 focus:ring-pink-200'
              }`}
            />
            {errors.itemName && <span className="text-[11px] text-rose-500 mt-1 block">{errors.itemName.message}</span>}
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">ชื่อลูกค้า / แบรนด์</label>
            <input 
              type="text" 
              placeholder="เช่น คุณมิลิน (Soft Studio)"
              {...register("customer", { required: "กรุณากรอกชื่อลูกค้า" })}
              className={`w-full px-4 py-2.5 rounded-2xl border text-sm focus:outline-none focus:ring-2 transition-all ${
                errors.customer ? 'border-rose-300 focus:ring-rose-200' : 'border-slate-200 focus:ring-pink-200'
              }`}
            />
            {errors.customer && <span className="text-[11px] text-rose-500 mt-1 block">{errors.customer.message}</span>}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">จำนวน (ตัว)</label>
              <input 
                type="number" 
                min="1"
                {...register("quantity", { required: true, min: 1 })}
                className="w-full px-4 py-2.5 rounded-2xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-pink-200"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">กำหนดส่ง</label>
              <input 
                type="text" 
                {...register("dueDate", { required: true })}
                className="w-full px-4 py-2.5 rounded-2xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-pink-200"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <button 
              type="button" 
              onClick={handleCloseModal}
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
}

export default CreateOrderModal