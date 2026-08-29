'use client';

import { useState, useEffect } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';

interface Transaction {
  transaction_id: string;
  from_account: string;
  to_account: string;
  amount: number;
  transaction_type: string;
  metadata: any;
  created_at: string;
}

export default function BillingPage() {
  const [balance, setBalance] = useState(0);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBillingData();
    const interval = setInterval(fetchBillingData, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchBillingData = async () => {
    try {
      const [balanceRes, transactionsRes] = await Promise.all([
        fetch('http://localhost:8000/api/ledger/balance/customer:customer-demo-001'),
        fetch('http://localhost:8000/api/ledger/transactions?account_id=customer:customer-demo-001&limit=20')
      ]);
      
      const balanceData = await balanceRes.json();
      const transactionsData = await transactionsRes.json();
      
      setBalance(balanceData.balance || 0);
      setTransactions(transactionsData.transactions || []);
    } catch (error) {
      console.error('Failed to fetch billing data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTransactionTypeColor = (type: string) => {
    switch (type) {
      case 'deposit': return 'text-emerald-400';
      case 'withdrawal': return 'text-red-400';
      case 'payment': return 'text-blue-400';
      case 'refund': return 'text-yellow-400';
      default: return 'text-slate-400';
    }
  };

  const getTransactionSign = (tx: Transaction) => {
    if (tx.to_account.includes('customer-demo-001')) {
      return '+';
    }
    return '-';
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Billing & Tokens</h1>
          <p className="text-slate-400 mt-1">CLSTR token balance and transaction history</p>
        </div>

        {/* Balance Card */}
        <div className="bg-gradient-to-br from-indigo-500/20 to-violet-500/20 rounded-lg p-6 border border-indigo-500/30">
          <div className="text-slate-300 text-sm mb-2">Current Balance</div>
          <div className="text-4xl font-bold text-white mb-1">
            {balance.toLocaleString()} CLSTR
          </div>
          <div className="text-slate-400 text-sm">
            ≈ ${(balance * 0.01).toFixed(2)} USD
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
            <div className="text-slate-400 text-sm">Total Earned</div>
            <div className="text-2xl font-bold text-emerald-400 mt-1">
              {transactions
                .filter(tx => tx.to_account.includes('customer-demo-001'))
                .reduce((sum, tx) => sum + tx.amount, 0)
                .toLocaleString()} CLSTR
            </div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
            <div className="text-slate-400 text-sm">Total Spent</div>
            <div className="text-2xl font-bold text-red-400 mt-1">
              {transactions
                .filter(tx => tx.from_account.includes('customer-demo-001'))
                .reduce((sum, tx) => sum + tx.amount, 0)
                .toLocaleString()} CLSTR
            </div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
            <div className="text-slate-400 text-sm">Transactions</div>
            <div className="text-2xl font-bold text-slate-100 mt-1">
              {transactions.length}
            </div>
          </div>
        </div>

        {/* Transaction History */}
        <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden">
          <div className="p-4 border-b border-slate-700/50">
            <h2 className="text-lg font-semibold text-slate-100">Transaction History</h2>
          </div>
          
          {loading ? (
            <div className="p-8 text-center text-slate-400">Loading transactions...</div>
          ) : transactions.length === 0 ? (
            <div className="p-8 text-center text-slate-400">No transactions yet</div>
          ) : (
            <div className="divide-y divide-slate-700/50">
              {transactions.map((tx) => (
                <div key={tx.transaction_id} className="p-4 hover:bg-slate-700/30 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-1">
                        <span className={`text-sm font-medium ${getTransactionTypeColor(tx.transaction_type)}`}>
                          {tx.transaction_type.toUpperCase()}
                        </span>
                        <span className="text-slate-400 text-sm">
                          {tx.metadata?.description || 'Transaction'}
                        </span>
                      </div>
                      <div className="text-xs text-slate-500 font-mono">
                        {tx.transaction_id}
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <div className={`text-lg font-bold ${
                        getTransactionSign(tx) === '+' ? 'text-emerald-400' : 'text-red-400'
                      }`}>
                        {getTransactionSign(tx)}{tx.amount.toLocaleString()} CLSTR
                      </div>
                      <div className="text-xs text-slate-500">
                        {new Date(tx.created_at).toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
