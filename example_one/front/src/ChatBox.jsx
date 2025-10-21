import 'bootstrap/dist/css/bootstrap.min.css';
import { useEffect, useMemo, useRef, useState } from "react";
import { Container, Card, Form, Button, InputGroup } from "react-bootstrap";
import OpenAI from "openai";

function ChatBox() {
	const [input, setInput] = useState("");
	const [messages, setMessages] = useState([]);
	const [showCard, setShowCard] = useState(false);

	const scrollRef = useRef(null);

	const openaiApiKey = import.meta.env.VITE_OPENAI_API_KEY;
	const client = new OpenAI({
		apiKey: openaiApiKey,
		dangerouslyAllowBrowser: true
	});
	// stream type
	const streamType = {
		created : "response.created",
		completed : "response.completed",
		error : "error",
		failed : "response.failed",
		in_progress : "response.in_progress",
		incomplete : "response.incomplete",
		output_item_added : "response.output_item.added",
		output_item_done : "response.output_item.done",
		content_part_added : "response.content_part.added",
		content_part_done : "response.content_part.done",
		output_text_delta : "response.output_text.delta",
		output_text_done : "response.output_text.done"
	};

	const send = async () => {
		const text = input.trim();
		if (!text) return;
		const now = Date.now();
		setMessages(prev => [
			...prev,
			{ id: now, role: "user", content: text },
		]);
		setInput("");
		if (!showCard) setShowCard(true);
		try {
			const stream = await client.responses.create({
				model: "gpt-5",
				input: [
					{
						role: "user",
						content: text,
					},
				],
				stream: true,
			});
			/* 
			stream flow :
			created -> in_progress -> output_item_added -> output_item_done
			-> output_item_added -> content_part_added -> output_text_delta (until end of delta input)
			-> output_text_done -> content_part_done -> output_item_done -> response_completed
			If a new conte
			*/
			for await (const event of stream) {
				// console.log("Stream event:", event);
				if (event.type === streamType.created){
					// handle created event
					var timestamp = event.response.created_at;
					// create a new message
					setMessages(prev => [
						...prev,
						{ id: timestamp, role: "backend", content: ""}
					]);
				}
				else if (event.type === streamType.completed) {
					console.log("Response completed!");
					break;
				}
				// else if (event.type === streamType.output_item_added) {
				// 	console.log("Output item added.", event.item);
				// }
				// else if (event.type === streamType.output_item_done) {
				// 	console.log("Output item done.", event.item);
				// }
				// else if (event.type === streamType.content_part_added) {
				// 	console.log("Content part added");
				// }
				// else if (event.type === streamType.content_part_done) {
				// 	console.log("Content part done");
				// }
				else if (event.type === streamType.output_text_delta) {
					setMessages(prev => {
						return prev.map( item => {
							if (item.id === timestamp) {
								return {
									...item,
									content: item.content + event.delta
								};
							}
							return item;
						});
					});
				}
				// else if (event.type === streamType.output_text_done) {
				// 	console.log("Output text delta done!");
				// }
			}
			if (!showCard) setShowCard(true);
		} catch (error) {
			setMessages(prev => [
				...prev,
				{ id: now + 1, role: "backend", content: error.message }
			]);
		}
	};

	const onKeyDown = e => {
		if (e.key === "Enter" && !e.shiftKey) {
			e.preventDefault();
			send();
		}
	};

	useEffect(() => {
		const el = scrollRef.current;
		if (el) el.scrollTop = el.scrollHeight;
	}, [messages]);

	const items = useMemo(() => messages.map(m => (
		<Bubble key={m.id} role={m.role} content={m.content} />
	)), [messages]);

	return (
		<Container fluid className="mb-3 py-4 flex-column gap-3">
			{showCard && (
				<Card className="shadow-sm mb-3">
					<Card.Body
						ref={scrollRef}
						className="overflow-auto d-flex flex-column gap-2"
						style={{ height: "60vh" }}
					>
						{items.length ? items : <EmptyState text="Start the conversation below" />}
					</Card.Body>
				</Card>
			)}
			<div className="mb-3 d-flex justify-content-center w-100">
				<Form
					onSubmit={e => { e.preventDefault(); send(); }}
					className="d-flex gap-2 align-items-end p-2 border rounded-4"
					style={{ width: "min(1000px, 70vw)" }}
				>
					<InputGroup className="mb-3">
						<Form.Control
							id="user-input"
							placeholder="Type what you want to know… (Enter to send, Shift+Enter for newline)"
							value={input}
							onChange={e => setInput(e.target.value)}
							onKeyDown={onKeyDown}
						/>
						<Button type="submit" variant="outline-secondary" id="button-addon2">
						Button
						</Button>
					</InputGroup>
				</Form>
			</div>
		</Container>
	);
}

function Bubble({ role, content }) {
	const isUser = role === "user";
	return (
		<div className={`d-flex ${isUser ? "justify-content-end" : "justify-content-start"}`}>
		<div
			className={`rounded-4 px-3 py-2 shadow-sm ${
			isUser ? "bg-primary-subtle text-primary-emphasis" : "bg-light text-body"
			}`}
			style={{ maxWidth: "90%" }}
		>
			{content}
		</div>
		</div>
	);
}

function EmptyState({ text }) {
	return (
		<div className="flex-fill d-flex align-items-center justify-content-center text-secondary" style={{ minHeight: 80 }}>
		<span className="small">{text}</span>
		</div>
	);
}

export default ChatBox;