import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Zap, Server, Shield, TrendingUp, ArrowRight } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-purple-50">
      {}
      <header className="border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900">
                ClusterCloud
              </span>
            </div>
            <Link href="/dashboard">
              <Button>Go to Dashboard</Button>
            </Link>
          </div>
        </div>
      </header>

      {}
      <section className="max-w-7xl mx-auto px-6 py-24">
        <div className="text-center max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 bg-primary-100 text-primary-700 px-4 py-2 rounded-full text-sm font-medium mb-8">
            <Zap className="w-4 h-4" />
            Distributed Computing Made Simple
          </div>

          <h1 className="text-6xl font-bold text-gray-900 mb-6 leading-tight">
            Build Your Cloud.
            <br />
            <span className="bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent">
              Not Your Infrastructure.
            </span>
          </h1>

          <p className="text-xl text-gray-600 mb-12 max-w-2xl mx-auto">
            Skip the complexity. Tell us what you need, and we'll build the
            perfect distributed cloud for your workload—automatically.
          </p>

          <div className="flex items-center justify-center gap-4">
            <Link href="/dashboard">
              <Button size="lg" className="gap-2">
                Get Started
                <ArrowRight className="w-5 h-5" />
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button size="lg" variant="outline">
                View Demo
              </Button>
            </Link>
          </div>

          {}
          <div className="grid grid-cols-3 gap-8 mt-16 max-w-2xl mx-auto">
            <div>
              <div className="text-3xl font-bold text-gray-900 mb-1">10x</div>
              <div className="text-sm text-gray-600">Faster setup</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-gray-900 mb-1">100%</div>
              <div className="text-sm text-gray-600">Automated</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-gray-900 mb-1">
                24/7
              </div>
              <div className="text-sm text-gray-600">Self-healing</div>
            </div>
          </div>
        </div>
      </section>

      {}
      <section className="max-w-7xl mx-auto px-6 py-24">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            How It Works
          </h2>
          <p className="text-xl text-gray-600">
            Three simple steps to distributed computing
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {}
          <div className="bg-white rounded-2xl p-8 border border-gray-200 shadow-sm">
            <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center mb-6">
              <span className="text-2xl font-bold text-primary-600">1</span>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">
              Tell Us Your Needs
            </h3>
            <p className="text-gray-600">
              What are you rendering? How fast? What's your budget? Just answer
              a few simple questions.
            </p>
          </div>

          {}
          <div className="bg-white rounded-2xl p-8 border border-gray-200 shadow-sm">
            <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center mb-6">
              <span className="text-2xl font-bold text-primary-600">2</span>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">
              We Build Your Cloud
            </h3>
            <p className="text-gray-600">
              Our AI selects the perfect nodes, schedules your workload, and
              optimizes for speed and cost.
            </p>
          </div>

          {}
          <div className="bg-white rounded-2xl p-8 border border-gray-200 shadow-sm">
            <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center mb-6">
              <span className="text-2xl font-bold text-primary-600">3</span>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">
              Watch It Run
            </h3>
            <p className="text-gray-600">
              Real-time monitoring, automatic recovery, and transparent
              economics. All managed for you.
            </p>
          </div>
        </div>
      </section>

      {}
      <section className="max-w-7xl mx-auto px-6 py-24">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="text-4xl font-bold text-gray-900 mb-6">
              Focus on creating.
              <br />
              Not managing infrastructure.
            </h2>
            <p className="text-lg text-gray-600 mb-8">
              Traditional cloud platforms force you to be a systems engineer.
              ClusterCloud lets you stay a creator. Tell us what you need, and
              we handle the rest.
            </p>

            <div className="space-y-6">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Shield className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 mb-1">
                    Self-Healing
                  </h3>
                  <p className="text-gray-600">
                    Node failures? We automatically reassign your work to
                    healthy providers.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <TrendingUp className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 mb-1">
                    Transparent Economics
                  </h3>
                  <p className="text-gray-600">
                    Every token tracked. Fair penalties. Automatic compensation.
                    No surprises.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Server className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 mb-1">
                    Real Distribution
                  </h3>
                  <p className="text-gray-600">
                    Actual multi-node parallelism. Not fake cloud marketing.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-primary-500 to-purple-600 rounded-2xl p-12 text-white">
            <div className="space-y-8">
              <div>
                <div className="text-5xl font-bold mb-2">8 sec</div>
                <div className="text-primary-100">Average task assignment</div>
              </div>
              <div>
                <div className="text-5xl font-bold mb-2">99.9%</div>
                <div className="text-primary-100">Recovery success rate</div>
              </div>
              <div>
                <div className="text-5xl font-bold mb-2">5%</div>
                <div className="text-primary-100">Platform fee (transparent)</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {}
      <section className="max-w-7xl mx-auto px-6 py-24">
        <div className="bg-gradient-to-r from-primary-600 to-purple-600 rounded-3xl p-12 text-center text-white">
          <h2 className="text-4xl font-bold mb-4">
            Ready to build your cloud?
          </h2>
          <p className="text-xl text-primary-100 mb-8 max-w-2xl mx-auto">
            Join the future of distributed computing. No credit card required.
          </p>
          <Link href="/dashboard">
            <Button size="lg" variant="secondary" className="gap-2">
              <Zap className="w-5 h-5" />
              Get Started Free
            </Button>
          </Link>
        </div>
      </section>

      {}
      <footer className="border-t border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
                <Zap className="w-4 h-4 text-white" />
              </div>
              <span className="font-semibold text-gray-900">ClusterCloud</span>
            </div>
            <div className="text-sm text-gray-600">
              © 2024 ClusterCloud. Distributed computing made simple.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
