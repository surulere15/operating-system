"""
NUCLEAR SWARM DEPLOYMENT - MASTER CONTROL
Launch the complete aggressive trading system for 474% monthly target

This integrates:
- Nuclear Swarm Orchestrator (100 positions)
- WebSocket Manager (real-time data)
- Real-Time Dashboard (monitoring)
- All 5 trading strategies
- Circuit breakers & risk management

READY TO DEPLOY
"""

import asyncio
import sys
import time
from datetime import datetime
from typing import Dict, Any
import logging

# Import our components
from nuclear_swarm_orchestrator import NuclearSwarmOrchestrator
from realtime_dashboard import RealtimeDashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'nuclear_swarm_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class NuclearSwarmDeployment:
    """
    Master deployment controller for nuclear swarm trading system

    Coordinates:
    - Swarm orchestrator
    - Real-time dashboard
    - WebSocket feeds
    - Risk management
    - Performance tracking
    """

    def __init__(self,
                 initial_capital: float = 500,
                 mode: str = 'PAPER',  # 'PAPER' or 'LIVE'
                 target_monthly_return: float = 4.74):

        self.mode = mode
        self.initial_capital = initial_capital
        self.target_monthly_return = target_monthly_return
        self.target_daily_return = 0.0639  # 6.39% for 474% monthly

        # Initialize components
        logger.info("🌊 Initializing NUCLEAR SWARM DEPLOYMENT")
        logger.info(f"   Mode: {mode}")
        logger.info(f"   Capital: ${initial_capital:,.2f}")
        logger.info(f"   Target: {target_monthly_return*100:.0f}% monthly ({self.target_daily_return*100:.2f}% daily)")

        # Create swarm orchestrator
        self.swarm = NuclearSwarmOrchestrator(total_capital=initial_capital)

        # Create dashboard
        self.dashboard = RealtimeDashboard(
            target_monthly_return=target_monthly_return,
            refresh_interval=2  # 2 second refresh
        )

        # Deployment state
        self.is_running = False
        self.start_time = None
        self.cycles_completed = 0
        self.emergency_stop = False

    def pre_flight_checks(self) -> bool:
        """
        Pre-flight safety checks before deployment

        Returns: True if all checks pass
        """
        logger.info("🔍 Running pre-flight checks...")

        checks = []

        # Check 1: Capital available
        if self.swarm.total_capital > 0:
            checks.append(("Capital Available", True, f"${self.swarm.total_capital:,.2f}"))
        else:
            checks.append(("Capital Available", False, "No capital"))

        # Check 2: Strategies loaded
        if len(self.swarm.strategies) == 5:
            checks.append(("Strategies Loaded", True, "5/5 strategies"))
        else:
            checks.append(("Strategies Loaded", False, f"Only {len(self.swarm.strategies)}/5"))

        # Check 3: Symbols configured
        if len(self.swarm.active_symbols) >= 10:
            checks.append(("Symbols Configured", True, f"{len(self.swarm.active_symbols)} symbols"))
        else:
            checks.append(("Symbols Configured", False, f"Only {len(self.swarm.active_symbols)} symbols"))

        # Check 4: Swarm capacity
        if self.swarm.max_concurrent_positions >= 50:
            checks.append(("Swarm Capacity", True, f"{self.swarm.max_concurrent_positions} positions"))
        else:
            checks.append(("Swarm Capacity", False, f"Only {self.swarm.max_concurrent_positions} positions"))

        # Check 5: Dashboard ready
        if self.dashboard is not None:
            checks.append(("Dashboard Ready", True, "Monitoring active"))
        else:
            checks.append(("Dashboard Ready", False, "No dashboard"))

        # Print results
        print("\n" + "=" * 100)
        print("🔍 PRE-FLIGHT CHECKS")
        print("=" * 100)

        all_passed = True
        for check_name, passed, details in checks:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {status} | {check_name:<25} | {details}")
            if not passed:
                all_passed = False

        print("=" * 100)

        if all_passed:
            print("✅ ALL CHECKS PASSED - READY FOR DEPLOYMENT")
        else:
            print("❌ SOME CHECKS FAILED - FIX ISSUES BEFORE DEPLOYMENT")

        print("=" * 100 + "\n")

        return all_passed

    def display_deployment_banner(self):
        """Display deployment banner"""
        print("\n" + "=" * 100)
        print("🚀 NUCLEAR SWARM DEPLOYMENT - LAUNCHING")
        print("=" * 100)
        print(f"""
    Mode:                {self.mode}
    Initial Capital:     ${self.initial_capital:,.2f}
    Target Monthly:      {self.target_monthly_return*100:.0f}% (${self.initial_capital * self.target_monthly_return:,.2f})
    Target Daily:        {self.target_daily_return*100:.2f}%

    Swarm Configuration:
    - Symbols:           {len(self.swarm.active_symbols)}
    - Strategies:        {len(self.swarm.strategies)}
    - Max Positions:     {self.swarm.max_concurrent_positions}
    - Total Combinations: {self.swarm.calculate_total_combinations()}

    Risk Management:
    - Circuit Breakers:  ACTIVE
    - Position Limits:   {self.swarm.min_position_size_pct*100:.1f}% - {self.swarm.max_position_size_pct*100:.1f}% per position
    - Max Utilization:   {self.swarm.max_concurrent_positions} concurrent positions

    Start Time:          {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """)
        print("=" * 100)

        if self.mode == 'LIVE':
            print("\n⚠️  WARNING: LIVE TRADING MODE - REAL MONEY AT RISK ⚠️")
            print("=" * 100 + "\n")

    def run_cycle(self):
        """Run one swarm cycle"""
        try:
            # Execute swarm cycle
            self.swarm.swarm_cycle()
            self.cycles_completed += 1

            # Update dashboard
            swarm_status = self.swarm.get_status()

            # Convert to dashboard format
            orchestrator_status = {
                'timestamp': datetime.now(),
                'capital': swarm_status['capital'],
                'trades': {
                    'total': swarm_status['swarm']['total_closed'],
                    'total_wins': int(swarm_status['swarm']['win_rate'] * swarm_status['swarm']['total_closed']),
                    'total_losses': int((1 - swarm_status['swarm']['win_rate']) * swarm_status['swarm']['total_closed']),
                    'overall_win_rate': swarm_status['swarm']['win_rate']
                },
                'strategies': {
                    'nuclear_swarm': {
                        'status': 'active',
                        'trades': swarm_status['swarm']['active_positions'],
                        'win_rate': swarm_status['swarm']['win_rate'],
                        'pnl': swarm_status['capital']['total_pnl'],
                        'daily_pnl': swarm_status['capital']['daily_pnl'],
                        'allocated_capital': swarm_status['capital']['deployed']
                    }
                },
                'risk': {
                    'circuit_breaker_active': self.emergency_stop,
                    'circuit_breaker_reason': 'Emergency stop activated' if self.emergency_stop else None,
                    'drawdown_pct': max(0, ((swarm_status['capital']['total'] - self.initial_capital) / self.initial_capital) * -100)
                },
                'target': {
                    'daily_target_pct': self.target_daily_return * 100,
                    'daily_progress_pct': swarm_status['capital']['daily_return_pct'],
                    'on_track': swarm_status['capital']['daily_return_pct'] >= self.target_daily_return * 100,
                    'elapsed_days': (datetime.now() - self.start_time).total_seconds() / 86400 if self.start_time else 0,
                    'monthly_projection': ((1 + swarm_status['capital']['daily_return_pct']/100) ** 30 - 1) * 100 if swarm_status['capital']['daily_return_pct'] > 0 else 0
                }
            }

            # Render dashboard
            self.dashboard.render(orchestrator_status)

            # Check for alerts
            self.dashboard.check_alerts(orchestrator_status)

            # Log cycle completion
            logger.info(f"Cycle {self.cycles_completed} complete | "
                       f"Active: {swarm_status['swarm']['active_positions']} | "
                       f"Daily: {swarm_status['capital']['daily_return_pct']:+.2f}% | "
                       f"Total: {swarm_status['capital']['total_return_pct']:+.2f}%")

            # Check for emergency stop conditions
            if swarm_status['capital']['total_return_pct'] < -15:
                self.emergency_stop = True
                logger.critical("🚨 EMERGENCY STOP: Total loss >15%")

            if swarm_status['capital']['daily_return_pct'] < -10:
                self.emergency_stop = True
                logger.critical("🚨 EMERGENCY STOP: Daily loss >10%")

        except Exception as e:
            logger.error(f"Error in swarm cycle: {e}", exc_info=True)
            self.emergency_stop = True

    async def deploy(self, duration_hours: float = 24):
        """
        Deploy nuclear swarm for specified duration

        Args:
            duration_hours: How long to run (default 24 hours)
        """
        self.start_time = datetime.now()
        self.is_running = True

        logger.info(f"🚀 DEPLOYMENT STARTED - Running for {duration_hours} hours")

        end_time = self.start_time + timedelta(hours=duration_hours)
        cycle_interval = 10  # 10 seconds between cycles

        while self.is_running and datetime.now() < end_time:
            if self.emergency_stop:
                logger.critical("🚨 EMERGENCY STOP ACTIVATED - HALTING ALL TRADING")
                break

            # Run swarm cycle
            self.run_cycle()

            # Wait for next cycle
            await asyncio.sleep(cycle_interval)

        # Deployment ended
        self.is_running = False
        end_time_actual = datetime.now()
        duration_actual = (end_time_actual - self.start_time).total_seconds() / 3600

        logger.info(f"🛑 DEPLOYMENT ENDED - Ran for {duration_actual:.2f} hours")

        # Print final summary
        self.print_final_summary()

    def print_final_summary(self):
        """Print final deployment summary"""
        status = self.swarm.get_status()

        print("\n" + "=" * 100)
        print("📊 NUCLEAR SWARM DEPLOYMENT - FINAL SUMMARY")
        print("=" * 100)

        print(f"\n⏱️  DEPLOYMENT DURATION:")
        duration = (datetime.now() - self.start_time).total_seconds() / 3600
        print(f"   Started:  {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Ended:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Duration: {duration:.2f} hours ({self.cycles_completed} cycles)")

        print(f"\n💰 FINANCIAL RESULTS:")
        print(f"   Initial Capital:    ${self.initial_capital:,.2f}")
        print(f"   Final Capital:      ${status['capital']['total']:,.2f}")
        print(f"   Total P&L:          ${status['capital']['total_pnl']:+,.2f}")
        print(f"   Total Return:       {status['capital']['total_return_pct']:+.2f}%")
        print(f"   Daily Return:       {status['capital']['daily_return_pct']:+.2f}%")

        print(f"\n🐝 SWARM PERFORMANCE:")
        print(f"   Total Positions Opened:  {status['swarm']['total_opened']}")
        print(f"   Total Positions Closed:  {status['swarm']['total_closed']}")
        print(f"   Win Rate:                {status['swarm']['win_rate']*100:.1f}%")
        print(f"   Peak Utilization:        {status['swarm']['active_positions']} / {status['swarm']['max_capacity']}")

        print(f"\n🔍 OPPORTUNITY STATS:")
        print(f"   Opportunities Scanned:   {status['opportunities']['scanned']}")
        print(f"   Opportunities Taken:     {status['opportunities']['taken']}")
        print(f"   Acceptance Rate:         {status['opportunities']['acceptance_rate']:.1f}%")

        print(f"\n🎯 TARGET PROGRESS:")
        print(f"   Monthly Target:          {self.target_monthly_return*100:.0f}%")
        monthly_projection = ((1 + status['capital']['daily_return_pct']/100) ** 30 - 1) * 100
        print(f"   Monthly Projection:      {monthly_projection:.1f}%")

        if monthly_projection >= self.target_monthly_return * 100:
            print(f"   Status:                  ✅ ON TRACK FOR TARGET")
        else:
            shortfall = self.target_monthly_return * 100 - monthly_projection
            print(f"   Status:                  ⚠️ Shortfall: {shortfall:.1f}%")

        print("\n" + "=" * 100)

        if status['capital']['total_pnl'] > 0:
            print("✅ DEPLOYMENT PROFITABLE - MISSION SUCCESS")
        else:
            print("❌ DEPLOYMENT UNPROFITABLE - REVIEW AND ADJUST")

        print("=" * 100 + "\n")


async def main():
    """Main deployment entry point"""

    print("""
    ╔════════════════════════════════════════════════════════════════════════════════════════════════╗
    ║                                                                                                ║
    ║                        🌊 NUCLEAR SWARM TRADING SYSTEM 🌊                                      ║
    ║                                                                                                ║
    ║                           474% Monthly Target Deployment                                       ║
    ║                                                                                                ║
    ╚════════════════════════════════════════════════════════════════════════════════════════════════╝
    """)

    # Configuration
    INITIAL_CAPITAL = 500
    MODE = 'PAPER'  # Change to 'LIVE' for real trading
    DURATION_HOURS = 24  # 24 hour test run

    # Create deployment
    deployment = NuclearSwarmDeployment(
        initial_capital=INITIAL_CAPITAL,
        mode=MODE,
        target_monthly_return=4.74
    )

    # Pre-flight checks
    if not deployment.pre_flight_checks():
        logger.error("Pre-flight checks failed. Aborting deployment.")
        return

    # Get user confirmation
    deployment.display_deployment_banner()

    print("\n⚠️  FINAL CONFIRMATION REQUIRED ⚠️")
    print("=" * 100)
    print(f"You are about to deploy the NUCLEAR SWARM with ${INITIAL_CAPITAL:,.2f} capital")
    print(f"Mode: {MODE}")
    print(f"Duration: {DURATION_HOURS} hours")
    print("=" * 100)

    confirmation = input("\nType 'DEPLOY' to confirm deployment: ")

    if confirmation != 'DEPLOY':
        logger.info("Deployment cancelled by user")
        print("\n❌ DEPLOYMENT CANCELLED\n")
        return

    # Deploy!
    logger.info("🚀 DEPLOYMENT CONFIRMED - LAUNCHING NUCLEAR SWARM")
    print("\n🚀 NUCLEAR SWARM LAUNCHING...\n")

    try:
        await deployment.deploy(duration_hours=DURATION_HOURS)
    except KeyboardInterrupt:
        logger.info("Deployment interrupted by user (Ctrl+C)")
        deployment.is_running = False
        deployment.print_final_summary()
    except Exception as e:
        logger.error(f"Deployment error: {e}", exc_info=True)
        deployment.emergency_stop = True
        deployment.print_final_summary()


if __name__ == '__main__':
    # Run deployment
    asyncio.run(main())
