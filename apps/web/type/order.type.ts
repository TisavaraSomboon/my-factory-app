export type Order = {
    id: string,
    itemName: string,
    customer: string,
    quantity: 120,
    currentStep: 4,
    status: Status,
    dueDate: string,
    failedDate: string,
    failReason: string,
    resources: {
      machineHours: string,
      fabricUsed: string,
      laborCount: string,
    },
    logs: [
      { step: 1, note: string, time: string },
      { step: 2, note: string, time: string },
      { step: 3, note: string, time: string },
    ]
}

export enum Status {
    IN_PROGRESS = 'in_progress',
    COMPLETED = 'completed',
    FAILED = 'failed'
}