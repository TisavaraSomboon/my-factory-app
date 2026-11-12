'use client'

import {Shirt, Package, AlertCircle} from 'lucide-react'
import { usePathname, useRouter } from 'next/navigation'

const Navbar = () => {
    const router = useRouter()
    const pathname = usePathname()

    {/* Top Navigation Bar */}
    return <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-md border-b border-pink-100/80 px-6 py-4">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          {/* Brand Logo */}
          <div 
            onClick={() => { router.push('/') }}
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
              onClick={() => { router.push('/') }}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300 flex items-center gap-2 ${
                pathname === '/' || pathname.includes('/order')
                  ? 'bg-white text-pink-600 shadow-sm scale-100' 
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <Package className="w-4 h-4" />
              รายการผลิต 
              3
              {/*({activeOrders.length})*/}
            </button>

            <button
              onClick={() => { router.push("/holding-order") }}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300 flex items-center gap-2 ${
                pathname === '/holding-order'
                  ? 'bg-rose-50 text-rose-600 shadow-sm ring-1 ring-rose-200' 
                  : 'text-slate-500 hover:text-rose-500'
              }`}
            >
              <AlertCircle className="w-4 h-4" />
              จัดส่งไม่สำเร็จ
              2
              {/* {failedOrders.length > 0 && (
                <span className="px-2 py-0.5 text-xs bg-rose-200 text-rose-700 rounded-full animate-pulse">
                  {failedOrders.length}
                </span>
              )} */}
            </button>
          </nav>
        </div>
      </header>
}

export default Navbar