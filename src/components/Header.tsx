import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { Menu, MessageSquareText, BookText, Settings, LogOut, History, UserCircle2 } from 'lucide-react';
import { useAuth } from '../hooks/useAuth'; // Update the path as needed based on your project structure
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useEffect, useState } from 'react';
import { getUserHistory, HistoryItem } from '@/services/historyService';
import { toast } from '@/components/ui/use-toast';
import { cn } from '@/lib/utils';

const navLinks = [
	{ href: '/', label: 'Home', icon: <MessageSquareText className="h-5 w-5" /> },
	{ href: '/speech-error', label: 'Speech Error Analysis', icon: <MessageSquareText className="h-5 w-5" /> },
	{ href: '/grammar-check', label: 'Grammar Check', icon: <BookText className="h-5 w-5" /> },
	{ href: '/concept-summarization', label: 'Concept Summarization', icon: <BookText className="h-5 w-5" /> },
	{ href: '/chorus', label: 'Chorus', icon: <BookText className="h-5 w-5" /> },
	// Add other main feature links here
];

const accountLinks = [
	{ href: '/profile', label: 'Profile', icon: <UserCircle2 className="h-5 w-5" /> },
	{ href: '/settings', label: 'Settings', icon: <Settings className="h-5 w-5" /> },
];

export function Header() {
	const { user, logout } = useAuth(); // Assuming useAuth provides user and logout
	const [history, setHistory] = useState<HistoryItem[]>([]);
	const [isHistoryOpen, setIsHistoryOpen] = useState(false);

	const fetchHistory = async () => {
		if (user) {
			try {
				const historyData = await getUserHistory();
				setHistory(historyData.history);
			} catch (error: any) {
				console.error('Failed to fetch history:', error);
				toast({
					title: 'Error fetching history',
					description: error.message || 'Could not load your activity history.',
					variant: 'destructive',
				});
			}
		}
	};

	useEffect(() => {
		if (isHistoryOpen && user) {
			fetchHistory();
		}
	}, [isHistoryOpen, user]);

	const handleLogout = () => {
		logout();
		// Optionally redirect or show a toast message
		toast({ title: 'Logged out successfully' });
	};

	const formatHistoryTimestamp = (timestamp: string) => {
		return new Date(timestamp).toLocaleString();
	};

	const getFeaturePath = (feature: string, details: any) => {
		switch (feature) {
			case 'speech_error_analysis':
				return '/speech-error'; // Or a more specific path if details allow
			case 'grammar_check':
				return '/grammar-check';
			case 'summarize_concept':
				return '/concept-summarization';
			case 'tts_google':
			case 'texttospeech_custom':
				return '/chorus'; // Now these features link to the chorus page
			default:
				return '/';
		}
	};

	return (
		<header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
			<div className="container flex h-14 items-center">
				<div className="mr-4 hidden md:flex">
					<Link to="/" className="mr-6 flex items-center space-x-2">
						{/* <YourLogo className="h-6 w-6" /> */}
						<span className="font-bold sm:inline-block">EduSpeak</span>
					</Link>
					<nav className="flex items-center space-x-6 text-sm font-medium">
						{navLinks.map((link) => (
							<Link
								key={link.label}
								to={link.href}
								className="transition-colors hover:text-foreground/80 text-foreground/60"
							>
								{link.label}
							</Link>
						))}
					</nav>
				</div>

				{/* Mobile Menu & History Sidebar Trigger */}
				<Sheet>
					<SheetTrigger asChild>
						<Button variant="ghost" size="icon" className="md:hidden">
							<Menu className="h-5 w-5" />
							<span className="sr-only">Toggle Menu</span>
						</Button>
					</SheetTrigger>
					<SheetContent side="left" className="pr-0">
						<SheetHeader>
							<SheetTitle>
								<Link to="/" className="flex items-center space-x-2">
									{/* <YourLogo className="h-6 w-6" /> */}
									<span className="font-bold">EduSpeak</span>
								</Link>
							</SheetTitle>
						</SheetHeader>
						<ScrollArea className="my-4 h-[calc(100vh-8rem)] pb-10 pl-6">
							<div className="flex flex-col space-y-3">
								{navLinks.map((link) => (
									<Link
										key={link.label}
										to={link.href}
										className="flex items-center space-x-2 transition-colors hover:text-foreground"
									>
										{link.icon}
										<span>{link.label}</span>
									</Link>
								))}
							</div>
							{user && (
								<>
									<Separator className="my-4" />
									<div className="flex flex-col space-y-3">
										<h4 className="font-medium">My Account</h4>
										{accountLinks.map((link) => (
											<Link
												key={link.label}
												to={link.href}
												className="flex items-center space-x-2 transition-colors hover:text-foreground"
											>
												{link.icon}
												<span>{link.label}</span>
											</Link>
										))}
										<Button
											variant="ghost"
											onClick={handleLogout}
											className="justify-start px-0 hover:text-destructive"
										>
											<LogOut className="mr-2 h-5 w-5" />
											Logout
										</Button>
									</div>
								</>
							)}
						</ScrollArea>
					</SheetContent>
				</Sheet>

				<div className="flex flex-1 items-center justify-between space-x-2 md:justify-end">
					{user && (
						<Sheet open={isHistoryOpen} onOpenChange={setIsHistoryOpen}>
							<SheetTrigger asChild>
								<Button variant="ghost" size="icon">
									<History className="h-5 w-5" />
									<span className="sr-only">View History</span>
								</Button>
							</SheetTrigger>
							<SheetContent className="w-[400px] sm:w-[540px]">
								<SheetHeader>
									<SheetTitle>Activity History</SheetTitle>
								</SheetHeader>
								<ScrollArea className="h-[calc(100vh-8rem)] py-4">
									{history.length > 0 ? (
										<div className="space-y-4">
											{history.map((item, index) => (
												<Link
													to={getFeaturePath(item.feature, item.details)}
													key={index}
													className="block p-3 hover:bg-muted/50 rounded-md border"
												>
													<div className="font-semibold text-sm capitalize">
														{item.feature.replace(/_/g, ' ')}
													</div>
													<div className="text-xs text-muted-foreground">
														{formatHistoryTimestamp(item.timestamp)}
													</div>
													{item.details && (
														<div className="mt-1 text-xs text-muted-foreground truncate">
															{typeof item.details === 'string'
																? item.details
																: item.details.text_length
																? `Text Length: ${item.details.text_length}`
																: item.details.filename
																? `File: ${item.details.filename}`
																: item.details.concept_length
																? `Concept Length: ${item.details.concept_length}`
																: JSON.stringify(item.details).substring(0, 100) +
																  (JSON.stringify(item.details).length > 100 ? '...' : '')}
														</div>
													)}
												</Link>
											))}
										</div>
									) : (
										<p className="text-sm text-muted-foreground">No history yet.</p>
									)}
								</ScrollArea>
							</SheetContent>
						</Sheet>
					)}
					{!user && (
						<Button asChild>
							<Link to="/login">Login</Link>
						</Button>
					)}
				</div>
			</div>
		</header>
	);
}
