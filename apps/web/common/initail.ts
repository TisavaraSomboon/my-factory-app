export const INITIAL_ORDERS = [
  {
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
  },
  {
    id: 'ORD-2026-002',
    itemName: 'Cotton Apron (Kitchen Series)',
    customer: 'Bake & Bloom Cafe',
    quantity: 50,
    currentStep: 2,
    status: 'in_progress',
    dueDate: '25 พ.ย. 2026',
    resources: {
      machineHours: '8 / 24 ชม.',
      fabricUsed: '60 เมตร',
      laborCount: '2 คน',
    },
    logs: [
      { step: 1, note: 'สร้างแพทเทิร์นผ้ากันเปื้อนเสร็จสมบูรณ์', time: '12 พ.ย. 10:00' },
    ]
  },
  {
    id: 'ORD-2026-003',
    itemName: 'Oversized Knit Cardigan',
    customer: 'Cozy Wear BKK',
    quantity: 200,
    currentStep: 6,
    status: 'completed',
    dueDate: '12 พ.ย. 2026',
    resources: {
      machineHours: '96 / 96 ชม.',
      fabricUsed: '310 เมตร',
      laborCount: '8 คน',
    },
    logs: [
      { step: 6, note: 'แพ็คลงกล่องและส่งมอบให้ขนส่งเรียบร้อยแล้ว', time: '12 พ.ย. 14:00' },
    ]
  },
  {
    id: 'ORD-2026-004',
    itemName: 'Silk Pajama Set (Mint)',
    customer: 'Dreamy Night Shop',
    quantity: 80,
    currentStep: 6,
    status: 'failed',
    failReason: 'ไม่พบผู้รับปลายทาง (ที่อยู่จัดส่งไม่ชัดเจน) และกล่องพัสดุชำรุด 2 ลังระหว่างขนส่ง',
    failedDate: '11 พ.ย. 2026',
    dueDate: '11 พ.ย. 2026',
    resources: {
      machineHours: '64 / 64 ชม.',
      fabricUsed: '140 เมตร',
      laborCount: '5 คน',
    },
    logs: [
      { step: 5, note: 'ผ่านการตรวจ QA 100%', time: '10 พ.ย. 16:00' },
      { step: 6, note: 'ตีกลับสินค้าเนื่องจากขนส่งไม่สามารถติดต่อผู้รับได้', time: '11 พ.ย. 17:45' },
    ]
  },
  {
    id: 'ORD-2026-005',
    itemName: 'Canvas Tote Bag (Custom Print)',
    customer: 'Artisan Market',
    quantity: 300,
    currentStep: 5,
    status: 'failed',
    failReason: 'ไม่ผ่านเกณฑ์ QA รอบสุดท้าย (สีสกรีนเพี้ยนจาก Pantone) ตีกลับแก้ไขและล่าช้าเกินกำหนดส่ง',
    failedDate: '12 พ.ย. 2026',
    dueDate: '12 พ.ย. 2026',
    resources: {
      machineHours: '50 / 48 ชม.',
      fabricUsed: '220 เมตร',
      laborCount: '4 คน',
    },
    logs: [
      { step: 5, note: 'QA ตรวจพบสีสกรีนไม่ตรงมาตรฐาน ส่งกลับแก้ไขด่วน', time: '12 พ.ย. 09:15' },
    ]
  }
];