
from ns import ns
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--per", type=float, default=0.005)
parser.add_argument("--bandwidth", default="2Mbps")
parser.add_argument("--delay", default="0.01ms")
parser.add_argument("--simTime", type=float, default=20.0)
args = parser.parse_args()

if not 0 <= args.per <= 1 or args.simTime <= 1:
    parser.error("PER must be 0..1 and simTime must exceed 1 second")

# Chọn TCP Westwood+
tcp_type = ns.TypeId.LookupByName("ns3::TcpWestwoodPlus")
ns.Config.SetDefault(
    "ns3::TcpL4Protocol::SocketType",
    ns.TypeIdValue(tcp_type)
)

# Kích thước TCP segment
ns.Config.SetDefault(
    "ns3::TcpSocket::SegmentSize",
    ns.UintegerValue(400)
)

# Tạo ba nút: Source, Router, Sink
nodes = ns.NodeContainer()
nodes.Create(3)

# Liên kết Source - Router
access = ns.PointToPointHelper()
access.SetDeviceAttribute("DataRate", ns.StringValue("10Mbps"))
access.SetChannelAttribute("Delay", ns.StringValue("45ms"))

d1 = access.Install(nodes.Get(0), nodes.Get(1))

# Liên kết Router - Sink
bottleneck = ns.PointToPointHelper()
bottleneck.SetDeviceAttribute(
    "DataRate", ns.StringValue(args.bandwidth)
)
bottleneck.SetChannelAttribute(
    "Delay", ns.StringValue(args.delay)
)

d2 = bottleneck.Install(nodes.Get(1), nodes.Get(2))

# Mô hình lỗi gói tin trên liên kết bottleneck

# Tạo RateErrorModel thông qua ObjectFactory
factory = ns.ObjectFactory()
factory.SetTypeId("ns3::RateErrorModel")

factory.Set(
    "ErrorRate",
    ns.DoubleValue(args.per)
)

factory.Set(
    "ErrorUnit",
    ns.StringValue("ERROR_UNIT_PACKET")
)

# Tạo đối tượng từ factory
error = factory.Create[ns.RateErrorModel]()

# Gắn mô hình lỗi vào thiết bị nhận
d2.Get(1).SetAttribute(
    "ReceiveErrorModel",
    ns.PointerValue(error)
)

# Cài đặt TCP/IP
stack = ns.InternetStackHelper()
stack.Install(nodes)

address = ns.Ipv4AddressHelper()
address.SetBase(
    ns.Ipv4Address("10.1.1.0"),
    ns.Ipv4Mask("255.255.255.0")
)
address.Assign(d1)

address.SetBase(
    ns.Ipv4Address("10.1.2.0"),
    ns.Ipv4Mask("255.255.255.0")
)
interfaces = address.Assign(d2)

ns.Ipv4GlobalRoutingHelper.PopulateRoutingTables()

# Ứng dụng nhận TCP
port = 5000
sink_address = ns.InetSocketAddress(
    ns.Ipv4Address.GetAny(),
    port
)

sink = ns.PacketSinkHelper(
    "ns3::TcpSocketFactory",
    sink_address.ConvertTo()
)

sink_app = sink.Install(nodes.Get(2))
sink_app.Start(ns.Seconds(0))
sink_app.Stop(ns.Seconds(args.simTime))

# Ứng dụng gửi TCP
destination = ns.InetSocketAddress(
    interfaces.GetAddress(1),
    port
)

source = ns.BulkSendHelper(
    "ns3::TcpSocketFactory",
    destination.ConvertTo()
)

source.SetAttribute("MaxBytes", ns.UintegerValue(0))
source.SetAttribute("SendSize", ns.UintegerValue(400))

source_app = source.Install(nodes.Get(0))
source_app.Start(ns.Seconds(1))
source_app.Stop(ns.Seconds(args.simTime))

# Chạy mô phỏng
ns.Simulator.Stop(ns.Seconds(args.simTime))
ns.Simulator.Run()

# Đo lượng dữ liệu nhận được
sink_ptr = sink_app.Get(0).GetObject[ns.PacketSink]()
received_bytes = sink_ptr.GetTotalRx()

throughput = (
    received_bytes * 8.0
    / ((args.simTime - 1.0) * 1000000.0)
)

print("TCP: TcpWestwoodPlus")
print("PER:", args.per)
print("Bandwidth:", args.bandwidth)
print("Delay:", args.delay)
print("Received bytes:", received_bytes)
print("Throughput:", throughput, "Mbps")

ns.Simulator.Destroy()
