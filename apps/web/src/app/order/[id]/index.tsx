"use client"
import { useParams } from 'next/navigation'

const Order = () => {
    const {id } = useParams()
    return <div>
        <div className='text-xl text-bold'>order id: {id}</div>
        </div>
}

export default Order