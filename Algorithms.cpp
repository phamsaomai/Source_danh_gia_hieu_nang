
#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/error-model.h"
#include "ns3/tcp-westwood.h"

#include <iostream>
#include <string>
#include <stdint.h>

using namespace ns3;

int main(int argc, char *argv[])
{
    // ==========================================
    // 1. THAM SO MO PHONG
    // ==========================================

    std::string tcp = "WestwoodPlus";
    std::string bandwidth = "2Mbps";
    std::string delay = "0.01ms";

    double per = 0.005;
    double simTime = 20.0;
    uint32_t delAck = 1;

    CommandLine cmd;
    cmd.AddValue("tcp", "TCP variant", tcp);
    cmd.AddValue("per", "Packet Error Rate", per);
    cmd.AddValue("bandwidth", "Bottleneck bandwidth", bandwidth);
    cmd.AddValue("delay", "Bottleneck delay", delay);
    cmd.AddValue("simTime", "Simulation time", simTime);
    cmd.AddValue("delAck", "Delayed ACK count", delAck);
    cmd.Parse(argc, argv);

    if (per < 0.0 || per > 1.0 || simTime <= 1.0)
    {
        std::cerr << "Invalid PER or simulation time"
                  << std::endl;
        return 1;
    }

    // ==========================================
    // 2. LUA CHON THUAT TOAN TCP
    // ==========================================

    std::string socketType;

    if (tcp == "Westwood" || tcp == "WestwoodPlus")
    {
        socketType = "ns3::TcpWestwood";

        Config::SetDefault(
            "ns3::TcpWestwood::ProtocolType",
            StringValue(
                tcp == "Westwood"
                ? "Westwood"
                : "WestwoodPlus"
            )
        );
    }
    else if (tcp == "Reno")
    {
        socketType = "ns3::TcpReno";
    }
    else if (tcp == "NewReno")
    {
        socketType = "ns3::TcpNewReno";
    }
    else if (tcp == "Tahoe")
    {
        socketType = "ns3::TcpTahoe";
    }
    else
    {
        std::cerr << "Unknown TCP variant: "
                  << tcp << std::endl;
        return 1;
    }

    Config::SetDefault(
        "ns3::TcpL4Protocol::SocketType",
        TypeIdValue(TypeId::LookupByName(socketType))
    );

    // TCP segment size = 400 bytes
    Config::SetDefault(
        "ns3::TcpSocket::SegmentSize",
        UintegerValue(400)
    );

    // Delayed ACK
    Config::SetDefault(
        "ns3::TcpSocket::DelAckCount",
        UintegerValue(delAck)
    );

    // ==========================================
    // 3. TAO MO HINH MANG
    // ==========================================

    // Source --- Router --- Sink
    NodeContainer nodes;
    nodes.Create(3);

    // Source -> Router
    PointToPointHelper access;
    access.SetDeviceAttribute(
        "DataRate",
        StringValue("10Mbps")
    );
    access.SetChannelAttribute(
        "Delay",
        StringValue("45ms")
    );

    NetDeviceContainer d1 =
        access.Install(nodes.Get(0), nodes.Get(1));

    // Router -> Sink (bottleneck)
    PointToPointHelper bottleneck;
    bottleneck.SetDeviceAttribute(
        "DataRate",
        StringValue(bandwidth)
    );
    bottleneck.SetChannelAttribute(
        "Delay",
        StringValue(delay)
    );

    NetDeviceContainer d2 =
        bottleneck.Install(nodes.Get(1), nodes.Get(2));

    // ==========================================
    // 4. MO HINH LOI GOI TIN
    // ==========================================

    Ptr<RateErrorModel> error =
        CreateObject<RateErrorModel>();

    error->SetAttribute(
        "ErrorRate",
        DoubleValue(per)
    );

    error->SetAttribute(
        "ErrorUnit",
        EnumValue(RateErrorModel::ERROR_UNIT_PACKET)
    );

    // Gan loi tai dau nhan cua bottleneck
    d2.Get(1)->SetAttribute(
        "ReceiveErrorModel",
        PointerValue(error)
    );

    // ==========================================
    // 5. CAI DAT TCP/IP
    // ==========================================

    InternetStackHelper stack;
    stack.Install(nodes);

    Ipv4AddressHelper address;

    address.SetBase(
        "10.1.1.0",
        "255.255.255.0"
    );

    address.Assign(d1);

    address.SetBase(
        "10.1.2.0",
        "255.255.255.0"
    );

    Ipv4InterfaceContainer interfaces =
        address.Assign(d2);

    Ipv4GlobalRoutingHelper::PopulateRoutingTables();

    // ==========================================
    // 6. UNG DUNG NHAN TCP
    // ==========================================

    uint16_t port = 5000;

    PacketSinkHelper sink(
        "ns3::TcpSocketFactory",
        InetSocketAddress(
            Ipv4Address::GetAny(),
            port
        )
    );

    ApplicationContainer sinkApp =
        sink.Install(nodes.Get(2));

    sinkApp.Start(Seconds(0.0));
    sinkApp.Stop(Seconds(simTime));

    // ==========================================
    // 7. UNG DUNG GUI TCP
    // ==========================================

    BulkSendHelper source(
        "ns3::TcpSocketFactory",
        InetSocketAddress(
            interfaces.GetAddress(1),
            port
        )
    );

    source.SetAttribute(
        "MaxBytes",
        UintegerValue(0)
    );

    source.SetAttribute(
        "SendSize",
        UintegerValue(400)
    );

    ApplicationContainer sourceApp =
        source.Install(nodes.Get(0));

    sourceApp.Start(Seconds(1.0));
    sourceApp.Stop(Seconds(simTime));

    // ==========================================
    // 8. CHAY MO PHONG
    // ==========================================

    Simulator::Stop(Seconds(simTime));
    Simulator::Run();

    // ==========================================
    // 9. TINH THROUGHPUT
    // ==========================================

    Ptr<PacketSink> sinkPtr =
        DynamicCast<PacketSink>(sinkApp.Get(0));

    uint64_t receivedBytes =
        sinkPtr->GetTotalRx();

    double throughput =
        receivedBytes * 8.0 /
        ((simTime - 1.0) * 1000000.0);

    // ==========================================
    // 10. IN KET QUA
    // ==========================================

    std::cout << "TCP: " << tcp << std::endl;
    std::cout << "PER: " << per << std::endl;
    std::cout << "Bandwidth: " << bandwidth << std::endl;
    std::cout << "Delay: " << delay << std::endl;
    std::cout << "Delayed ACK: " << delAck << std::endl;

    std::cout << "Received bytes: "
              << receivedBytes << std::endl;

    std::cout << "Throughput: "
              << throughput << " Mbps"
              << std::endl;

    Simulator::Destroy();

    return 0;
}
